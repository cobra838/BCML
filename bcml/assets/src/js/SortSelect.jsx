import React from "react";
import ReactSortable from "react-sortablejs";
import { ThemeProvider } from "react-bootstrap";

class ModSelect extends React.Component {
    constructor() {
        super();
        this.state = {
            selectedItems: [],
            mods: [],
            justSorted: false,
            lastSelectedPriority: null
        };
    }

    componentDidMount() {
        this.setState({
            mods: this.props.mods,
            selectedItems: [this.props.mods[0].priority],
            lastSelectedPriority: this.props.mods[0].priority
        });
    }

    static getDerivedStateFromProps(nextProps, prevState) {
        if (JSON.stringify(nextProps.mods) != JSON.stringify(prevState.mods)) {
            return {
                mods: nextProps.mods,
                selectedItems: [nextProps.mods[0].priority],
                lastSelectedPriority: nextProps.mods[0].priority
            };
        } else return null;
    }

    componentDidUpdate(prevProps, prevState) {
        if (prevState.selectedItems != this.state.selectedItems) {
            const selectedMods = this.state.mods.filter(
                mod =>
                    this.state.selectedItems.includes(mod.priority) &&
                    !mod.path.startsWith("QUEUE")
            );
            this.props.onSelect(selectedMods);
            if (selectedMods.length > 0) {
                let query = `[id='mod-${selectedMods[0].id}']`;
                try {
                    document.querySelector(query).scrollIntoView();
                } catch (err) {
                    console.log(query);
                }
            }

            return;
        }
        if (JSON.stringify(prevProps.mods) != JSON.stringify(this.state.mods)) {
            this.setState({
                selectedItems: this.state.justSorted ? prevState.selectedItems : [],
                justSorted: false
            });
        }
    }

    onItemSelect(e, mod) {
        e.persist();
        if (mod.path.startsWith("QUEUE")) return;
        const visibleMods = this.state.mods.filter(
            item => !item.path.startsWith("QUEUE") && (this.props.showDisabled || !item.disabled)
        );
        let items;
        if (
            e.shiftKey &&
            this.state.lastSelectedPriority &&
            visibleMods.some(item => item.priority === this.state.lastSelectedPriority)
        ) {
            const start = visibleMods.findIndex(
                item => item.priority === this.state.lastSelectedPriority
            );
            const end = visibleMods.findIndex(item => item.priority === mod.priority);
            const range = visibleMods
                .slice(Math.min(start, end), Math.max(start, end) + 1)
                .map(item => item.priority);
            items = e.ctrlKey
                ? [...new Set([...this.state.selectedItems, ...range])]
                : range;
        } else if (!this.state.selectedItems.includes(mod.priority)) {
            if (!e.ctrlKey) items = [mod.priority];
            else items = [mod.priority, ...this.state.selectedItems];
        } else {
            if (e.ctrlKey) {
                items = this.state.selectedItems.filter(
                    priority => priority !== mod.priority
                );
            } else {
                items = [mod.priority];
            }
        }
        this.setState({
            selectedItems: items,
            lastSelectedPriority: mod.priority
        });
    }

    onSort(order, sortable, event) {
        const mod = JSON.parse(event.item.dataset.id);
        this.setState(
            prevState => ({
                selectedItems: !mod.path.startsWith("QUEUE")
                    ? [mod.priority]
                    : prevState.selectedItems,
                justSorted: true,
                lastSelectedPriority: !mod.path.startsWith("QUEUE")
                    ? mod.priority
                    : prevState.lastSelectedPriority
            }),
            () => this.props.onChange(order.map(mod => JSON.parse(mod)))
        );
    }

    render() {
        return (
            this.state.mods.length > 0 && (
                <ReactSortable
                    className="mod-list"
                    key={JSON.stringify(this.state.selectedItems)}
                    onChange={this.onSort.bind(this)}
                    options={{ handle: ".mod-handle" }}>
                    {this.state.mods.map(mod => (
                        <ModItem
                            key={JSON.stringify(mod)}
                            mod={mod}
                            active={this.state.selectedItems.includes(mod.priority)}
                            showHandle={this.props.showHandle}
                            hide={!this.props.showDisabled && mod.disabled}
                            onClick={e => this.onItemSelect(e, mod)}
                        />
                    ))}
                </ReactSortable>
            )
        );
    }
}

class ModItem extends React.Component {
    render() {
        let classes = ["list-group-item"];
        if (this.props.active) classes.push("active");
        if (this.props.hide) classes.push("d-none");
        if (this.props.mod.disabled) classes.push("mod-disabled");
        if (this.props.mod.path.startsWith("QUEUE")) classes.push("mod-queued");
        return (
            <div
                className={classes.join(" ")}
                onClick={this.props.onClick}
                data-id={JSON.stringify(this.props.mod)}
                id={`mod-${this.props.mod.id}`}>
                <span
                    className={
                        "mod-handle" + (!this.props.showHandle ? " d-none" : "")
                    }>
                    <i className="material-icons">drag_handle</i>
                </span>
                {this.props.mod.name}
            </div>
        );
    }
}

export default ModSelect;
