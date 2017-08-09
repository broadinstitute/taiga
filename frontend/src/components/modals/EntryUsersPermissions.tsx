import * as React from "react";
import * as Modal from "react-modal";
import {BootstrapTable, TableHeaderColumn, SelectRowMode, CellEditClickMode, CellEdit} from "react-bootstrap-table";

import {modalStyles} from "../Dialogs";

import {TaigaApi} from "../../models/api"

import {AccessLog} from "../../models/models";

interface EntryUsersPermissionsProps {
    isVisible: boolean;
    cancel: () => void;

    entry_id: string;
}

interface EntryUsersPermissionsState {
    accessLogs?: Array<AccessLog>;
}

let tapi: TaigaApi = null;

export class EntryUsersPermissions extends React.Component<EntryUsersPermissionsProps, EntryUsersPermissionsState> {
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    componentWillMount() {
        this.setState({
            accessLogs: []
        })
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        this.doFetch();
    }

    doFetch() {
        // Return access logs for this folder
        return tapi.get_entry_access_log(this.props.entry_id).then((usersAccessLogs) => {
            // TODO: Think about not using it as State because it does not change during the page lifecycle

            let mappedAL = usersAccessLogs.map((userAccessLogs) => {
                return new AccessLog(userAccessLogs);
            });

            this.setState({
                accessLogs: mappedAL
            })
        })
    }

    render() {
        const check_mode: SelectRowMode = 'checkbox';
        const selectRowProp = {
            mode: check_mode
        };

        return <Modal
            style={ modalStyles }
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}
            contentLabel="EditName">
            <div className="modal-content">
                <div className="modal-header">
                    <h3>Users Permissions</h3>
                </div>
                <div className="modal-body">
                    <BootstrapTable data={ this.state.accessLogs } search selectRow={ selectRowProp } deleteRow>
                        <TableHeaderColumn dataField='user_id' isKey hidden>User Id</TableHeaderColumn>
                        <TableHeaderColumn dataField='user_name'>User Name</TableHeaderColumn>
                        <TableHeaderColumn dataField="last_access">Last Access</TableHeaderColumn>
                    </BootstrapTable>
                </div>
                <div className="modal-footer">
                    <button type="button" className="btn btn-default">Close</button>
                </div>
            </div>
        </Modal>
    }
}