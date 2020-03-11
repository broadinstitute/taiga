import * as React from "react";
import { RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";

import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";

import { LeftNav } from "./LeftNav";

import { TaigaApi } from "../models/api";
import { Group } from "../models/models";

import { relativePath } from "../utilities/route";

export interface GroupListProps extends RouteComponentProps {
  tapi: TaigaApi;
  groups: Array<Pick<Group, Exclude<keyof Group, "users">>>;
}

export interface GroupListState {}

export class GroupListView extends React.Component<
  GroupListProps,
  GroupListState
> {
  groupLinkFormatter(
    cell: string,
    row: Pick<Group, Exclude<keyof Group, "users">>
  ) {
    return <Link to={relativePath("group/" + row.id)}>{cell}</Link>;
  }

  render() {
    let navItems: Array<any> = [];
    return (
      <div>
        <LeftNav items={navItems} />

        <div id="main-content">
          <h2>Your User Groups</h2>
          <BootstrapTable data={this.props.groups} striped>
            <TableHeaderColumn dataField="id" isKey hidden>
              ID
            </TableHeaderColumn>
            <TableHeaderColumn
              dataField="name"
              dataSort
              dataFormat={this.groupLinkFormatter}
            >
              Name
            </TableHeaderColumn>
            <TableHeaderColumn dataField="num_users" dataSort>
              Number of Users
            </TableHeaderColumn>
          </BootstrapTable>
        </div>
      </div>
    );
  }
}
