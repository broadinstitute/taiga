import * as React from "react";
import { RouteComponentProps } from "react-router";

import {
  Col,
  Grid,
  Row,
  OverlayTrigger,
  Tooltip,
  InputGroup,
  FormGroup,
  FormControl,
} from "react-bootstrap";

import ClipboardButton from "../utilities/r-clipboard";
import { LeftNav, MenuItem } from "./LeftNav";
import FigshareToken from "./modals/FigshareToken";

import TaigaApi from "../models/api";
import { User } from "../models/models";

export interface TokenProps extends RouteComponentProps {
  tapi: TaigaApi;
}

export interface TokenState {
  token: string;
  showFigshareTokenModel: boolean;
}

const antiPadding = {
  paddingLeft: "0px",
};

const clipboardButtonStyle = {};

export class Token extends React.Component<TokenProps, TokenState> {
  constructor(props: any) {
    super(props);

    this.state = {
      token: "",
      showFigshareTokenModel: false,
    };
  }

  componentDidMount() {
    this.doFetch();
  }

  doFetch() {
    this.props.tapi
      .get_user()
      .then((user: User) => {
        this.setState({
          token: user.token,
        });
      })
      .catch((err: any) => {
        console.log(err);
      });
  }

  render() {
    const navItems: Array<MenuItem> = [];

    navItems.push({
      label: "Connect to Figshare",
      action: () => {
        this.setState({ showFigshareTokenModel: true });
      },
    });

    const tooltipToken = (
      <Tooltip id="token_copy_confirmation">
        <strong>Copied!</strong>
      </Tooltip>
    );

    return (
      <div>
        <LeftNav items={navItems} />

        <div id="main-content">
          <Grid>
            <Row>
              <h1>Your token</h1>
            </Row>
            <Row>
              <p>
                Please, place the string below in <code>`~/.taiga/token`</code>{" "}
                to use taigaR and taigaPy.
              </p>
              <p>
                <a
                  href="https://github.com/broadinstitute/taigapy"
                  target="_blank"
                >
                  More information.
                </a>
              </p>
            </Row>
            <Row>
              <form>
                <FormGroup>
                  <Col xs={6} md={6} style={antiPadding}>
                    <InputGroup>
                      <FormControl
                        type="text"
                        readOnly
                        value={this.state.token}
                        style={{ cursor: "text" }}
                      />
                      <InputGroup.Button>
                        <OverlayTrigger
                          trigger="click"
                          placement="right"
                          overlay={tooltipToken}
                          rootClose
                        >
                          <ClipboardButton
                            data-clipboard-text={this.state.token}
                          >
                            {/* TODO: Clipboard Button breaks Glyphicon by not adding ::before...find a way to counter this */}
                            <span>Copy</span>
                          </ClipboardButton>
                        </OverlayTrigger>
                      </InputGroup.Button>
                    </InputGroup>
                  </Col>
                </FormGroup>
              </form>
            </Row>
          </Grid>
        </div>
        <FigshareToken
          tapi={this.props.tapi}
          show={this.state.showFigshareTokenModel}
          onHide={() => this.setState({ showFigshareTokenModel: false })}
        />
      </div>
    );
  }
}
