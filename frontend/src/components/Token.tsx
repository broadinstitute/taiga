import * as React from "react";
import { Grid, Row, OverlayTrigger, Tooltip } from 'react-bootstrap';

import ClipboardButton from '../Utilities/r-clipboard';
import { LeftNav } from "./LeftNav"

import { TaigaApi } from "../models/api"
import {User} from "../models/models";

export interface TokenProps {

}

export interface TokenState {
    token?: string;
}

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
                        <OverlayTrigger trigger="click" placement="right" overlay={tooltipToken} rootClose={true}>
                            <ClipboardButton className="btn btn-default" data-clipboard-text={this.state.token}>
                                {this.state.token}
                            </ClipboardButton>
                        </OverlayTrigger>
                    </Row>
                </Grid>
            </div>
        </div>
    }
}