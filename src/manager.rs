use crate::{
    settings::{ExportMethod, Settings, SwitchExportLayout, WiiuExportLayout},
    util, Result,
};
use anyhow::Context;
use fs_err as fs;
use join_str::jstr;
use parking_lot::RwLockReadGuard;
use pyo3::{prelude::*, Bound};
use rayon::prelude::*;
use serde::Deserialize;
#[cfg(windows)]
use remove_dir_all::remove_dir_all;
#[cfg(not(windows))]
use std::fs::remove_dir_all;
use std::path::{Path, PathBuf};
#[cfg(windows)]
use std::{fs as stdfs, io::ErrorKind};
#[cfg(windows)]
use std::{thread, time::Duration};

pub fn manager_mod(py: Python<'_>, parent: &Bound<'_, PyModule>) -> PyResult<()> {
    let manager_module = PyModule::new(py, "manager")?;
    manager_module.add_function(wrap_pyfunction!(link_master_mod, &manager_module)?)?;
    parent.add_submodule(&manager_module)?;
    Ok(())
}

static RULES_TXT: &str = r#"[Definition]
titleIds = 00050000101C9300,00050000101C9400,00050000101C9500
name = BCML
path = The Legend of Zelda: Breath of the Wild/Mods/BCML
description = Complete pack of mods merged using BCML
version = 7
default = true
fsPriority = 9999
"#;

#[derive(Debug, Default, Deserialize)]
struct StoredModOptions {
    #[serde(default)]
    selects: Vec<String>,
}

struct ModLinker<'py, 'set> {
    merged: PathBuf,
    output: Option<PathBuf>,
    needs_rules: bool,
    rules_path: PathBuf,
    settings: RwLockReadGuard<'set, Settings>,
    py: Python<'py>,
}

impl<'py, 'set> ModLinker<'py, 'set> {
    fn selected_option_dirs(mod_dir: &Path) -> Vec<PathBuf> {
        let options_dir = mod_dir.join("options");
        if !options_dir.is_dir() {
            return Vec::new();
        }
        let options_path = mod_dir.join("options.json");
        let stored: StoredModOptions = options_path
            .is_file()
            .then(|| fs::read_to_string(&options_path).ok())
            .flatten()
            .and_then(|text| serde_json::from_str(&text).ok())
            .unwrap_or_default();
        stored
            .selects
            .into_iter()
            .map(|folder| options_dir.join(folder))
            .filter(|folder| folder.is_dir())
            .collect()
    }

    fn new(py: Python<'py>, output: Option<PathBuf>) -> Self {
        let settings = util::settings();
        let merged = settings.merged_modpack_dir();
        Self {
            output,
            py,
            needs_rules: !settings.no_cemu && settings.wiiu,
            rules_path: merged.join("rules.txt"),
            merged,
            settings,
        }
    }

    fn link_internal(&self) -> Result<()> {
        let Self {
            merged,
            needs_rules,
            rules_path,
            settings,
            py,
            ..
        } = self;
        if merged.exists() {
            remove_dir_all(merged).context("Failed to clear internal merged folder")?;
        }
        fs::create_dir_all(merged).context("Failed to create internal merged folder")?;
        if *needs_rules && !rules_path.exists() {
            // Since for some incomprehensible reason hard-linking this from
            // the master folder randomly doesn't work, we'll just write it
            // straight to the merged folder.
            fs::write(rules_path, RULES_TXT).context("Failed to write rules.txt")?;
        }
        let mod_folders: Vec<PathBuf> =
            glob::glob(&settings.mods_dir().join("*").to_string_lossy())
                .expect("Bad glob?!?!?")
                .filter_map(|p| p.ok())
                .filter(|p| p.is_dir() && !p.join(".disabled").exists())
                .collect::<std::collections::BTreeSet<PathBuf>>()
                .into_iter()
                .flat_map(|p| {
                    std::iter::once(p.clone())
                        .chain(Self::selected_option_dirs(&p))
                        .collect::<Vec<PathBuf>>()
                })
                .collect();
        py.detach(|| -> Result<()> {
            mod_folders
                .into_iter()
                .rev()
                .try_for_each(|folder| -> Result<()> {
                    let mod_files: Vec<(PathBuf, PathBuf)> =
                        glob::glob(&folder.join("**/*").to_string_lossy())
                            .expect("Bad glob?!?!?!")
                            .filter_map(|p| {
                                p.ok().map(|p| {
                                    (p.clone(), unsafe {p.strip_prefix(&folder).unwrap_unchecked()}.to_owned())
                                })
                            })
                            .filter(|(item, rel)| {
                                !(merged.join(rel).exists()
                                    || item.is_dir()
                                    || item.extension().and_then(|e| e.to_str()) == Some("json")
                                    || rel.starts_with("logs")
                                    || rel.starts_with("options")
                                    || rel.starts_with("meta")
                                    || (rel.ancestors().count() == 1
                                        && rel.extension().and_then(|e| e.to_str())
                                            != Some("txt")
                                        && !item.is_dir()))
                            })
                            .collect();
                    mod_files
                        .into_par_iter()
                        .try_for_each(|(item, rel)| -> Result<()> {
                            let out = merged.join(&rel);
                            out.parent()
                                .map(fs::create_dir_all)
                                .transpose()
                                .with_context(|| jstr!("Failed to create parent folder for file {rel.to_str().unwrap()}"))?
                                .expect("Whoa, why is there no parent folder?");
                            fs::hard_link(&item, &out)
                                .with_context(|| jstr!("Failed to hard link {rel.to_str().unwrap()} to {out.to_str().unwrap()}"))
                                .or_else(|_| {
                                    eprintln!("Failed to hard link {} to {}", rel.display(), out.display());
                                    fs::copy(item, &out)
                                        .with_context(|| jstr!("Failed to copy {rel.to_str().unwrap()} to {out.to_str().unwrap()}"))
                                        .map(|_| ())
                                })?;
                            Ok(())
                        })?;
                    Ok(())
                })
        })?;
        Ok(())
    }

    fn remove_target(target: &PathBuf) -> Result<()> {
        #[cfg(windows)]
        {
            match stdfs::remove_dir(target) {
                Ok(()) => return Ok(()),
                Err(err) if err.kind() == ErrorKind::NotFound => return Ok(()),
                Err(_) => {}
            }
            if junction::exists(target).unwrap_or(false) {
                junction::delete(target).context("Failed to remove output junction")?;
                return Ok(());
            }
        }
        let meta = match fs::symlink_metadata(target) {
            Ok(meta) => meta,
            Err(err) if err.kind() == std::io::ErrorKind::NotFound => return Ok(()),
            Err(err) => return Err(err).context("Failed to stat output target"),
        };
        if meta.file_type().is_symlink() || meta.is_file() {
            fs::remove_file(target).context("Failed to remove output file link")?;
        } else {
            #[cfg(windows)]
            {
                match stdfs::remove_dir(target) {
                    Ok(()) => return Ok(()),
                    Err(err) if err.kind() == ErrorKind::NotFound => return Ok(()),
                    Err(_) => {}
                }
            }
            remove_dir_all(target).context("Failed to clear output folder")?;
        }
        Ok(())
    }

    #[cfg(windows)]
    fn ensure_target_removed(target: &PathBuf) -> Result<()> {
        for _ in 0..20 {
            Self::remove_target(target)?;
            if fs::symlink_metadata(target).is_err() {
                return Ok(());
            }
            thread::sleep(Duration::from_millis(25));
        }
        anyhow::bail!("Failed to remove existing output target: {}", target.display())
    }

    fn prepare_target_parent(target: &PathBuf) -> Result<()> {
        let Some(parent) = target.parent().map(PathBuf::from) else {
            return Ok(());
        };
        #[cfg(windows)]
        {
            if junction::exists(&parent).unwrap_or(false) {
                Self::remove_target(&parent)?;
            }
        }
        if let Ok(meta) = fs::symlink_metadata(&parent) {
            if meta.file_type().is_symlink() || meta.is_file() {
                Self::remove_target(&parent)?;
            }
        }
        fs::create_dir_all(&parent).context("Failed to create parent output folder")?;
        Ok(())
    }

    fn deploy_dir(method: ExportMethod, source: &PathBuf, target: &PathBuf) -> Result<()> {
        #[cfg(windows)]
        Self::ensure_target_removed(target)?;
        #[cfg(not(windows))]
        Self::remove_target(target)?;
        if !source.exists() {
            return Ok(());
        }
        Self::prepare_target_parent(target)?;
        match method {
            ExportMethod::Copy => {
                dircpy::copy_dir(source, target).context("Failed to copy output folder")?;
            }
            ExportMethod::HardLink => {
                #[cfg(windows)]
                junction::create(source, target).context("Failed to create output junction")?;
                #[cfg(unix)]
                std::os::unix::fs::symlink(source, target)
                    .context("Failed to create output symlink")?;
            }
            ExportMethod::Symlink => {
                #[cfg(windows)]
                std::os::windows::fs::symlink_dir(source, target)
                    .context("Failed to create output symlink")?;
                #[cfg(unix)]
                std::os::unix::fs::symlink(source, target)
                    .context("Failed to create output symlink")?;
            }
        }
        Ok(())
    }

    fn external_targets(&self) -> Option<(Vec<(PathBuf, PathBuf)>, Option<PathBuf>, ExportMethod)> {
        let method = if self.output.is_some() {
            ExportMethod::Copy
        } else {
            self.settings.export_method()
        };
        if let Some(output) = &self.output {
            return Some((
                vec![
                    (self.merged.join(util::content()), output.join(util::content())),
                    (self.merged.join(util::dlc()), output.join(util::dlc())),
                ],
                self.settings.wiiu.then(|| output.clone()),
                method,
            ));
        }
        let output_root = self.settings.export_dir()?;
        if self.settings.wiiu {
            let package_root = match self.settings.export_layout {
                WiiuExportLayout::WithNamedFolder => output_root.join("BreathOfTheWild_BCML"),
                WiiuExportLayout::WithoutNamedFolder => output_root,
            };
            Some((
                vec![
                    (
                        self.merged.join("content"),
                        package_root.join("content"),
                    ),
                    (
                        self.merged.join("aoc/0010"),
                        package_root.join("aoc/0010"),
                    ),
                ],
                Some(package_root),
                method,
            ))
        } else {
            let title_root = |title_id: &str| match self.settings.export_layout_nx {
                SwitchExportLayout::Atmosphere => output_root.join(title_id).join("romfs"),
                SwitchExportLayout::Emulator => output_root
                    .join(title_id)
                    .join("BreathOfTheWild_BCML")
                    .join("romfs"),
            };
            let targets = util::SWITCH_BASE_TITLE_IDS
                .iter()
                .map(|title_id| {
                    (
                        self.merged.join(util::SWITCH_CONTENT_PATH),
                        title_root(title_id),
                    )
                })
                .chain(util::SWITCH_DLC_TITLE_IDS.iter().map(|title_id| {
                    (
                        self.merged.join(util::SWITCH_DLC_PATH),
                        title_root(title_id),
                    )
                }))
                .collect();
            Some((
                targets,
                None,
                method,
            ))
        }
    }

    fn link_external(&mut self) -> Result<()> {
        let Some((targets, rules_root, method)) = self.external_targets() else {
            return Ok(());
        };
        for (source, target) in &targets {
            Self::deploy_dir(method, source, target)?;
        }
        if let Some(root) = rules_root {
            fs::create_dir_all(&root).context("Failed to create export root")?;
            if self.rules_path.exists() {
                fs::copy(&self.rules_path, root.join("rules.txt"))
                    .context("Failed to copy rules.txt")?;
            }
            let merged_patches = self.merged.join("patches");
            let out_patches = root.join("patches");
            if merged_patches.exists() {
                Self::deploy_dir(method, &merged_patches, &out_patches)?;
            } else {
                Self::remove_target(&out_patches)?;
            }
        }
        Ok(())
    }
}

#[pyfunction]
fn link_master_mod(py: Python, output: Option<String>) -> PyResult<()> {
    let output = output.map(PathBuf::from);
    let mut linker = ModLinker::new(py, output);
    linker
        .link_internal()
        .context("Failed to link internal merge")?;
    if linker.output.is_some() || linker.settings.export_dir().is_some() {
        linker
            .link_external()
            .context("Failed to export merged mods")?;
    }
    Ok(())
}
