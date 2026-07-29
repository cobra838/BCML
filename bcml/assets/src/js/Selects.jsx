import { Alert, Button, Form, Modal, OverlayTrigger, Tooltip } from "react-bootstrap";

import React from "react";

class SelectsDialog extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            folders: [],
            error: null
        };
        this.formRef = React.createRef();
        this.handleChange = this.handleChange.bind(this);
    }

    getInitialFolders = props => {
        if (Array.isArray(props.selected)) {
            return [...props.selected];
        }
        const folders = [];
        if (props.mod?.options?.multi) {
            folders.push(
                ...props.mod.options.multi
                    .map(m => (m.default ? m.folder : null))
                    .filter(Boolean)
            );
        }
        if (props.mod?.options?.single) {
            folders.push(
                ...props.mod.options.single
                    .map(group => {
                        const option = group.options.find(opt => opt.default);
                        return option ? option.folder : null;
                    })
                    .filter(Boolean)
            );
        }
        return folders;
    };

    componentDidUpdate(prevProps) {
        if (
            this.props.mod &&
            (!prevProps.mod ||
                prevProps.mod.options != this.props.mod.options ||
                prevProps.selected != this.props.selected ||
                (!prevProps.show && this.props.show))
        ) {
            this.setState({
                folders: this.getInitialFolders(this.props),
                error: null
            });
        }
    }

    handleChange(e, singleFolders = null) {
        e.persist();
        if (!e.currentTarget.checked) {
            this.setState({
                folders: this.state.folders.filter(f => f != e.currentTarget.value)
            });
        } else {
            if (singleFolders) {
                this.setState({
                    folders: [
                        ...this.state.folders.filter(
                            f => !singleFolders.includes(f)
                        ),
                        e.currentTarget.value
                    ]
                });
            } else {
                this.setState({
                    folders: [...this.state.folders, e.currentTarget.value]
                });
            }
        }
    }

    // get checked opt, not from options.json!!!!
    getCheckedFolders = () => {
        if (!this.formRef.current) {
            return this.state.folders;
        }
        return Array.from(
            this.formRef.current.querySelectorAll("input:checked")
        ).map(input => input.value);
    };

    submit = () => {
        const folders = this.getCheckedFolders();
        if (
            this.props.mod.options.single
                .filter(g => g.required)
                .some(
                    g => !g.options.some(opt => folders.includes(opt.folder))
                )
        ) {
            this.setState({
                error: "One or more required options have not been selected."
            });
        } else {
            this.setState({ error: null, folders });
            this.props.onSet(folders);
        }
    };

    render() {
        return (
            <Modal
                show={this.props.show}
                scrollable={true}
                onHide={this.props.onClose}
                class="selects">
                <Modal.Header closeButton>
                    <Modal.Title>
                        Select Options for {this.props.mod && this.props.mod.name}
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {this.state.error && (
                        <Alert variant="danger">{this.state.error}</Alert>
                    )}
                    <p>
                        {this.props.mod && this.props.mod.name} has customization
                        options. Please select the options you would like to use below.
                    </p>
                    <Form ref={this.formRef}>
                        {this.props.mod &&
                            this.props.mod.options.multi &&
                            Object.keys(this.props.mod.options.multi).length > 0 && (
                                <>
                                    <h5>Multiple Choice Options</h5>
                                    {this.props.mod.options.multi.map(m => (
                                        <Form.Group controlId={m.folder} key={m.folder}>
                                            <OverlayTrigger
                                                overlay={
                                                    <Tooltip>
                                                        {m.desc || "No description"}
                                                        <br /><code>{m.folder}</code>
                                                    </Tooltip>
                                                }>
                                                <Form.Check
                                                    type="checkbox"
                                                    checked={this.state.folders.includes(
                                                        m.folder
                                                    )}
                                                    label={m.name}
                                                    value={m.folder}
                                                    onChange={this.handleChange}
                                                />
                                            </OverlayTrigger>
                                        </Form.Group>
                                    ))}
                                </>
                            )}
                        {this.props.mod &&
                            this.props.mod.options.single &&
                            Object.keys(this.props.mod.options.single).length > 0 && (
                                <>
                                    <h5>Single Choice Options</h5>
                                    {this.props.mod.options.single.map(s => (
                                        <div key={s.name} className="radio-group my-2">
                                            <strong>
                                                {s.name}{" "}
                                                {s.required && (
                                                    <span
                                                        className="text-danger"
                                                        title="Required">
                                                        *
                                                    </span>
                                                )}
                                            </strong>
                                            <small className="my-1 d-block">
                                                {s.desc}
                                            </small>
                                            {s.options.map(opt => (
                                                <Form.Group
                                                    controlId={opt.folder}
                                                    key={opt.folder}>
                                                    <OverlayTrigger
                                                        overlay={
                                                            <Tooltip>
                                                                {opt.desc ||
                                                                    "No description"}
                                                                <br /><code>{opt.folder}</code>
                                                            </Tooltip>
                                                        }>
                                                        <Form.Check
                                                            type="checkbox"
                                                            name={s.name}
                                                            label={opt.name}
                                                            value={opt.folder}
                                                            checked={this.state.folders.includes(
                                                                opt.folder
                                                            )}
                                                            onChange={e =>
                                                                this.handleChange(
                                                                    e,
                                                                    s.options.map(
                                                                        option =>
                                                                            option.folder
                                                                    )
                                                                )
                                                            }
                                                        />
                                                    </OverlayTrigger>
                                                </Form.Group>
                                            ))}
                                        </div>
                                    ))}
                                </>
                            )}
                    </Form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={this.submit}>
                        OK
                    </Button>
                    <Button variant="secondary" onClick={this.props.onClose}>
                        Close
                    </Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

export default SelectsDialog;
