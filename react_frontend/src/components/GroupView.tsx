import * as React from "react";
import { RouteComponentProps } from "react-router";

import {
  BootstrapTable,
  TableHeaderColumn,
  InsertButton
} from "react-bootstrap-table";

import { LeftNav } from "./LeftNav";
import * as Dialogs from "./Dialogs";
import { NotFound } from "./NotFound";

import { TaigaApi } from "../models/api";
import { Group, User, UserNamedId } from "../models/models";
import update from "immutability-helper";

interface GroupViewMatchProps {
  groupId: string;
}

export interface GroupViewProps
  extends RouteComponentProps<GroupViewMatchProps> {
  tapi: TaigaApi;
}

export interface GroupViewState {
  group: Group;
  selection: ReadonlyArray<string>;
  showAddUsersDialog: boolean;
  errorMessage?: string;
  allUsers?: Array<User>;
}

export class GroupView extends React.Component<GroupViewProps, GroupViewState> {
  constructor(props: GroupViewProps) {
    super(props);

    this.state = {
      group: {
        name: null,
        id: null,
        users: [],
        num_users: 0
      },
      selection: [],
      showAddUsersDialog: false
    };
  }

  componentDidMount() {
    this.doFetch().then(() => {
      this.props.tapi.get_all_users().then((r: Array<User>) => {
        this.setState({ allUsers: r });
      });
    });
  }

  componentDidUpdate(prevProps: GroupViewProps) {
    if (prevProps.match.params.groupId != this.props.match.params.groupId) {
      this.doFetch();
    }
  }

  doFetch() {
    return this.props.tapi
      .get_group(this.props.match.params.groupId)
      .then((r: Group) => {
        this.setState({ group: r, errorMessage: null });
      })
      .catch((err: Error) => {
        this.setState({ errorMessage: err.message });
      });
  }

  handleInsertButtonClick() {
    this.setState({ showAddUsersDialog: true });
  }

  renderInsertButton() {
    return (
      <InsertButton
        btnText="Add users"
        onClick={() => this.handleInsertButtonClick()}
      />
    );
  }

  onCloseInsertDialog() {
    this.setState({ showAddUsersDialog: false });
  }

  onDeleteRow(selections: Array<string>) {
    return this.props.tapi.remove_group_user_associations(
      this.props.match.params.groupId,
      selections
    );
  }

  onRowSelect(row: UserNamedId, isSelected: Boolean, e: any) {
    let select_key = row.id;
    const original_selection: any = this.state.selection;

    let updated_selection: Array<string>;

    let index = original_selection.indexOf(select_key);
    if (index !== -1) {
      updated_selection = update(original_selection, {
        $splice: [[index, 1]]
      });
    } else {
      updated_selection = update(original_selection, {
        $push: [select_key]
      });
    }

    this.setState({ selection: updated_selection });
  }

  onAllRowsSelect(isSelected: Boolean, rows: Array<UserNamedId>) {
    const original_selection: ReadonlyArray<string> = this.state.selection;
    let updated_selection: ReadonlyArray<string> = original_selection;

    let select_key = null;
    let index = null;
    rows.forEach(row => {
      select_key = row.id;
      index = updated_selection.indexOf(select_key);

      if (index != -1) {
        updated_selection = update(updated_selection, {
          $splice: [[index, 1]]
        });
      } else {
        updated_selection = update(updated_selection, {
          $push: [select_key]
        });
      }
    });

    this.setState({ selection: updated_selection });
  }

  handleAddUsersToGroup(userIds: Array<string>) {
    return this.props.tapi
      .add_group_user_associations(this.state.group.id.toString(), userIds)
      .then((group: Group) => {
        this.setState({
          group: group,
          showAddUsersDialog: false
        });
      });
  }

  render() {
    let navItems: Array<any> = [];

    if (!!this.state.errorMessage) {
      const message =
        "Group ID " +
        this.props.match.params.groupId +
        " does not exist. Please check this id " +
        "is correct. We are also available via the feedback button.";
      return (
        <div>
          <LeftNav items={navItems} />
          <div id="main-content">
            <NotFound message={message} />
          </div>
        </div>
      );
    }

    const options = {
      deleteText: "Remove users",
      onDeleteRow: this.onDeleteRow.bind(this),
      insertBtn: this.renderInsertButton.bind(this)
    };
    const check_mode: any = "checkbox";
    const selectRowProp: any = {
      mode: check_mode,
      onSelect: (row: UserNamedId, isSelected: Boolean, e: any) => {
        this.onRowSelect(row, isSelected, e);
        return true;
      },
      onSelectAll: (
        isSelected: Boolean,
        currentSelectedAndDisplayData: Array<UserNamedId>
      ) => {
        this.onAllRowsSelect(isSelected, currentSelectedAndDisplayData);
        return true;
      }
    };
    return (
      <div>
        <LeftNav items={navItems} />

        <Dialogs.AddUsersToGroup
          group={this.state.group}
          allUsers={this.state.allUsers}
          addUsersToGroup={this.handleAddUsersToGroup.bind(this)}
          isVisible={this.state.showAddUsersDialog}
          cancel={this.onCloseInsertDialog.bind(this)}
        />

        <div id="main-content">
          <h2>{this.state.group.name}</h2>
          <BootstrapTable
            data={this.state.group.users}
            options={options}
            selectRow={selectRowProp}
            search
            insertRow
            deleteRow
            bordered={false}
            striped
            pagination
          >
            <TableHeaderColumn dataField="id" isKey hidden searchable={false}>
              ID
            </TableHeaderColumn>
            <TableHeaderColumn dataField="name" dataSort>
              User Name
            </TableHeaderColumn>
          </BootstrapTable>
        </div>
      </div>
    );
  }
}
