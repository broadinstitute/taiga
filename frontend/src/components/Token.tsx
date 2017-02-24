import * as React from "react";

import {Button, Col, Glyphicon, Grid, Row, OverlayTrigger, Tooltip, Well} from 'react-bootstrap';
import {InputGroup, InputGroupButton, form, FormGroup, FormControl} from 'react-bootstrap';

import ClipboardButton from '../utilities/r-clipboard';
import {LeftNav} from "./LeftNav"

import {TaigaApi} from "../models/api"
import {User} from "../models/models";

export interface TokenProps {

}

export interface TokenState {
    token?: string;
}

const inputTokenStyle = {
    width: '100%'
};

const clipboardButtonStyle = {};

let tapi: TaigaApi = null;

export class Token extends React.Component<TokenProps, TokenState> {
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    constructor(props: any) {
        super(props);

        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            token: 'Loading...'
        }
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        this.doFetch();
    }

    doFetch() {
        return tapi.get_user().then((user: User) => {
            this.setState({
                token: user.token
            })
        }).catch((err: any) => {
            console.log(err);
        });
    }

    render() {
        let navItems = [];

        const tooltipToken = (
            <Tooltip id="token_copy_confirmation"><strong>Copied!</strong></Tooltip>
        );

        return <div>
            <LeftNav items={navItems}/>

            <div id="main-content">
                <Grid>
                    <Row>
                        <h1>Your token</h1>
                    </Row>
                    <Row>
                        <form>
                            <FormGroup>
                                <Col xs={6} md={6}>
                                    <InputGroup>
                                        <FormControl
                                            type="text"
                                            disabled={true}
                                            placeholder={this.state.token}/>
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