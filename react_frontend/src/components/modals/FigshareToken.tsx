import * as React from "react";
import {
  Modal,
  FormGroup,
  FormControlProps,
  ControlLabel,
  FormControl,
  Button,
} from "react-bootstrap";
import TaigaApi from "../../models/api";

interface Props {
  tapi: TaigaApi;
  show: boolean;
  onHide: () => void;
}

interface State {
  token: string;
  tokenIsInvalid: boolean;
  success: boolean;
}

export default class FigshareToken extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      token: null,
      tokenIsInvalid: false,
      success: false,
    };
  }

  addToken = () => {
    this.props.tapi
      .authorize_figshare(this.state.token)
      .then(() => {
        this.setState({ success: true });
      })
      .catch((e) => {
        this.setState({ tokenIsInvalid: true });
      });
  };

  renderForm() {
    return (
      <>
        {" "}
        <Modal.Body>
          <p>
            Follow the instructions in Figshare's{" "}
            <a
              href="https://help.figshare.com/article/how-to-get-a-personal-token"
              rel="noopener"
              target="_blank"
            >
              How to get a Personal Token
            </a>{" "}
            article and enter the token in the box below.
          </p>
          <form>
            <FormGroup
              controlId="token"
              validationState={this.state.tokenIsInvalid ? "error" : null}
            >
              <ControlLabel>Personal token</ControlLabel>
              <FormControl
                type="text"
                value={this.state.token}
                onChange={(
                  event: React.FormEvent<FormControl & FormControlProps>
                ) =>
                  this.setState({
                    token: event.currentTarget.value as string,
                    tokenIsInvalid: false,
                  })
                }
              />
              <FormControl.Feedback />
            </FormGroup>
          </form>
        </Modal.Body>
        <Modal.Footer>
          <Button
            disabled={!this.state.token || this.state.tokenIsInvalid}
            onClick={this.addToken}
          >
            Connect
          </Button>
        </Modal.Footer>
      </>
    );
  }

  renderSuccess() {
    return (
      <>
        <Modal.Body>
          <p>Figshare personal token successfully added.</p>
        </Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() => {
              // Reset state
              this.setState({
                token: null,
                tokenIsInvalid: false,
                success: false,
              });

              // Close modal
              this.props.onHide();
            }}
          >
            Close
          </Button>
        </Modal.Footer>
      </>
    );
  }

  render() {
    return (
      <Modal show={this.props.show} onHide={this.props.onHide}>
        <Modal.Header closeButton>
          <Modal.Title>Connect to Figshare</Modal.Title>
        </Modal.Header>
        {this.state.success ? this.renderSuccess() : this.renderForm()}
      </Modal>
    );
  }
}
