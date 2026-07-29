import { Button, Form, InputGroup, OverlayTrigger } from "react-bootstrap";

import React from "react";

class FolderInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: "",
            valid: false
        };
        this.idRef = React.createRef();
        this.folderPick = this.folderPick.bind(this);
        this.handleChange = this.handleChange.bind(this);
        this.initialize = this.initialize.bind(this);
        this.updateValidity = this.updateValidity.bind(this);
    }

    async initialize() {
        this.id = this.idRef.current.id;
        this.setState({ value: this.props.value }, this.updateValidity);
    }

    async componentDidMount() {
        if (window.pywebview?.api) {
            this.initialize();
        } else {
            window.addEventListener("pywebviewready", this.initialize, { once: true });
        }
    }

    componentWillUnmount() {
        window.removeEventListener("pywebviewready", this.initialize);
    }

    updateValidity() {
        if (!window.pywebview?.api || !this.id) return;
        pywebview.api
            .dir_exists({
                folder: this.state.value,
                type: this.id
            })
            .then(valid => this.setState({ valid: valid && this.props.isValid }));
    }

    UNSAFE_componentWillReceiveProps(nextProps) {
        if (nextProps.value != this.state.value) {
            this.setState({ value: nextProps.value }, this.updateValidity);
        }
    }

    componentDidUpdate(_, prevState) {
        if (prevState.value != this.state.value) {
            this.props.onChange({
                target: { id: this.id, value: this.state.value }
            });
            this.updateValidity();
        }
    }

    folderPick() {
        if (!window.pywebview?.api) return;
        pywebview.api.get_folder({ type: this.id }).then(folder => this.setState({ value: folder || "" }));
    }

    handleChange(e) {
        e.persist();
        this.setState({ value: e.target.value });
    }

    render() {
        const overlay = this.props.overlay;
        return (
            <InputGroup>
                <OverlayTrigger
                    overlay={overlay}
                    placement={this.props.placement || "right"}>
                    <Form.Control
                        disabled={this.props.disabled}
                        placeholder={this.props.placeholder || "Select a directory"}
                        value={this.state.value}
                        onChange={this.handleChange}
                        ref={this.idRef}
                        isValid={this.state.valid}
                    />
                </OverlayTrigger>
                <InputGroup.Append>
                    <Button variant="secondary" onClick={this.folderPick}>
                        Browse...
                    </Button>
                </InputGroup.Append>
            </InputGroup>
        );
    }
}

export default FolderInput;
