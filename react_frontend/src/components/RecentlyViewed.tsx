import * as React from "react";
import { RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";

import { Grid, Row } from "react-bootstrap";

import {
  BootstrapTable,
  TableHeaderColumn,
  SortOrder
} from "react-bootstrap-table";

import { LeftNav } from "./LeftNav";

import { TaigaApi } from "../models/api";
import { AccessLog } from "../models/models";

import { lastAccessFormatter } from "../utilities/formats";

export interface RecentlyViewedProps extends RouteComponentProps {
  tapi: TaigaApi;
}

interface RecentlyViewedState {
  accessLogs?: Array<AccessLog>;
}

export class RecentlyViewed extends React.Component<
  RecentlyViewedProps,
  RecentlyViewedState
> {
  constructor(props: any) {
    super(props);

    this.state = {
      accessLogs: []
    };
  }

  componentDidMount() {
    this.doFetch();
  }

  doFetch() {
    return this.props.tapi.get_user_entry_access_log().then(userAccessLogs => {
      // TODO: Think about not using it as State because it does not change during the page lifecycle

      let mappedAL = userAccessLogs.map(userAccessLog => {
        return new AccessLog(userAccessLog);
      });

      this.setState({
        accessLogs: mappedAL
      });
    });
  }

  datasetFormatter(cell: any, row: any) {
    return <Link to={row.url}>{cell}</Link>;
  }

  render() {
    let navItems: Array<any> = [];

    let displayAccessLogs = null;

    const options = {
      defaultSortName: "last_access",
      defaultSortOrder: "desc" as any,
      sizePerPageList: [25, 30, 50, 100],
      sizePerPage: 50
    };

    if (this.state.accessLogs.length != 0) {
      displayAccessLogs = (
        <BootstrapTable
          data={this.state.accessLogs}
          striped
          hover
          options={options}
          pagination
        >
          <TableHeaderColumn isKey dataField="entry_id" hidden>
            Entry Id
          </TableHeaderColumn>
          <TableHeaderColumn
            dataField="entry_name"
            dataFormat={this.datasetFormatter}
            headerAlign="center"
            dataSort
          >
            Entry
          </TableHeaderColumn>
          <TableHeaderColumn
            dataField="last_access"
            headerAlign="center"
            dataAlign="center"
            dataFormat={lastAccessFormatter}
            dataSort
          >
            Last access
          </TableHeaderColumn>
        </BootstrapTable>
      );
    }

    return (
      <div>
        <LeftNav items={navItems} />

        <div id="main-content">
          <Grid>
            <Row>
              <h1>Your dataset access history</h1>
            </Row>
            <Row>{displayAccessLogs}</Row>
          </Grid>
        </div>
      </div>
    );
  }
}
