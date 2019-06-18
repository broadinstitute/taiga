import * as React from "react";
import * as PropTypes from "prop-types";
import * as Modal from "react-modal";
import { BootstrapTable, TableHeaderColumn, SelectRowMode, CellEditClickMode, CellEdit } from "react-bootstrap-table";

import { modalStyles } from "../Dialogs";

import { TaigaApi } from "../../models/api"

import { AccessLog } from "../../models/models";
import { lastAccessFormatter } from "../../utilities/formats";

interface EntryUsersPermissionsProps {
    isVisible: boolean;
    cancel: () => void;

    entry_id: string;

    handleDeletedRow: (arrayUserIds: Array<AccessLog>) => Promise<Function>;
}

interface EntryUsersPermissionsState {
    accessLogs?: Array<AccessLog>;
}

let tapi: TaigaApi = null;

export class EntryUsersPermissions extends React.Component<EntryUsersPermissionsProps, EntryUsersPermissionsState> {
    static contextTypes = {
        tapi: PropTypes.object
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

    componentWillReceiveProps(nextProps: any, nextState: any) {
        if (nextProps.entry_id != this.props.entry_id) {
            this.doFetch();
        }
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

    handleDeletedRow(rowKeys: any) {
        let state_accessLogs = this.state.accessLogs;
        let accessLogsToRemove = state_accessLogs.filter((accessLog) => {
            // TODO: Optimize this to not loop through the accessLogs array for each item
            for (let user_id of rowKeys) {
                if (user_id == accessLog.user_id) {
                    return true;
                }
            }
            return false;
        });
        this.props.handleDeletedRow(accessLogsToRemove).then(() => {
            // We update our list now
            this.doFetch();
        });
    }

    render() {
        const check_mode: any = 'checkbox';
        const selectRowProp = {
            mode: check_mode
        };

        const options = {
            afterDeleteRow: (rowKeys : any) => { this.handleDeletedRow(rowKeys) }
        };

        return <Modal
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}
            contentLabel="EditName">
            <div className="modal-content">
                <div className="modal-header">
                    <h3>Users Permissions</h3>
                </div>
                <div className="modal-body">
                    <BootstrapTable
                        data={this.state.accessLogs}
                        search
                        selectRow={selectRowProp}
                        deleteRow
                        options={options}>
                        <TableHeaderColumn dataField='user_id' isKey hidden>User Id</TableHeaderColumn>
                        <TableHeaderColumn dataField='user_name'>User Name</TableHeaderColumn>
                        <TableHeaderColumn
                            dataField="last_access"
                            dataFormat={lastAccessFormatter}>
                            Last Access
                        </TableHeaderColumn>
                    </BootstrapTable>
                </div>
                <div className="modal-footer">
                    <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
                </div>
            </div>
        </Modal>
    }
}