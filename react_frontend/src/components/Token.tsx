import * as React from "react";
import { RouteComponentProps } from "react-router";

import { Col, Grid, Row, OverlayTrigger, Tooltip } from "react-bootstrap";
import { InputGroup, FormGroup, FormControl } from "react-bootstrap";

import ClipboardButton from "../utilities/r-clipboard";
import { LeftNav, MenuItem } from "./LeftNav";

import { TaigaApi } from "../models/api";
import { User } from "../models/models";

export interface TokenProps extends RouteComponentProps {
    tapi: TaigaApi;
}

export interface TokenState {
    token?: string;
    figshareAuthUrl?: string;
}

const antiPadding = {
    paddingLeft: '0px'
};

const clipboardButtonStyle = {};


export class Token extends React.Component<TokenProps, TokenState> {
    constructor(props: any) {
        super(props);

        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            token: 'Loading...'
        }
    }

    componentDidMount() {
        this.doFetch();
    }

    doFetch() {
        this.props.tapi.get_user().then((user: User) => {
            this.setState({
                token: user.token
            })
        }).catch((err: any) => {
            console.log(err);
        });

        this.props.tapi.get_figshare_authorization_url().then(({figshare_auth_url}) => {
            this.setState({
                figshareAuthUrl: figshare_auth_url
            })
        }).catch((err: any) => {
            console.log(err);
        });
    }

    render() {
        let navItems: Array<MenuItem> = [];

        if (!!this.state.figshareAuthUrl) {
            navItems.push({
                label: "Connect to Figshare",
                action: () => {window.location.assign(this.state.figshareAuthUrl)}
            })
        }

        const tooltipToken = (
            <Tooltip id="token_copy_confirmation"><strong>Copied!</strong></Tooltip>
        );

        return <div>
            <LeftNav items={navItems} />

            <div id="main-content">
                <Grid>
                    <Row>
                        <h1>Your token</h1>
                    </Row>
                    <Row>
                        <p>
                            Please, place the string below in <code>`~/.taiga/token`</code> to use taigaR and taigaPy.
                        </p>
                        <p>
                            <a href="https://github.com/broadinstitute/taigapy" target="_blank">More information.</a>
                        </p>
                    </Row>
                    <Row>
                        <form>
                            <FormGroup>
                                <Col xs={6} md={6} style={antiPadding}>
                                    <InputGroup>
                                        <FormControl
                                            type="text"
                                            disabled={true}
                                            placeholder={this.state.token} />
                                        <InputGroup.Button>
                                            <OverlayTrigger trigger="click" placement="right" overlay={tooltipToken}
                                                rootClose={true}>
                                                <ClipboardButton className="btn btn-default"
                                                    style={clipboardButtonStyle}
                                                    data-clipboard-text={this.state.token}>
                                                    {/*TODO: Clipboard Button breaks Glyphicon by not adding ::before...find a way to counter this*/}
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
        </div>
    }
}