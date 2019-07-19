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
}

export interface GroupListState {
	groups: Array<Pick<Group, Exclude<keyof Group, "users">>>;
}

export class GroupListView extends React.Component<
	GroupListProps,
	GroupListState
> {
	constructor(props: GroupListProps) {
		super(props);

		this.state = {
			groups: []
		};
	}
	componentDidMount() {
		this.doFetch();
	}

	doFetch() {
		return this.props.tapi
			.get_all_groups_for_current_user()
			.then((r: any) => {
				this.setState(r);
			})
			.catch((err: any) => {
				console.log(err);
			});
	}

	groupLinkFormatter(cell: string, row: Pick<Group, Exclude<keyof Group, "users">>) {
		return <Link to={relativePath("group/" + row.id)}>{cell}</Link>;
	}

	render() {
		let navItems: Array<any> = [];
		return (
			<div>
				<LeftNav items={navItems} />

				<div id="main-content">
					<h2>Your User Groups</h2>
					<BootstrapTable data={this.state.groups} striped>
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
