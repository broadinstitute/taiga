import * as React from "react";
import { RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";
import * as update from "immutability-helper";

import { LeftNav, MenuItem } from "./LeftNav";
import * as Models from "../models/models";
import { TaigaApi } from "../models/api";

import { NotFound } from "./NotFound";
import { SearchInput } from "./Search";

import { toLocalDateString } from "../utilities/formats";
import { relativePath } from "../utilities/route";
import { LoadingOverlay } from "../utilities/loading";

import { Glyphicon } from "react-bootstrap";
import { Grid, Row, Col } from "react-bootstrap";
import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";
import { BootstrapTableSearchEntry } from "../models/models";

let _update: any = update;

interface SearchViewMatchParams {
  currentFolderId: string;
  searchQuery: string;
  folderId: string;
}

export interface SearchViewProps
  extends RouteComponentProps<SearchViewMatchParams> {
  tapi: TaigaApi;
}

const tableEntriesStyle: any = {
  margin: "initial",
};

export interface SearchViewState {
  // TODO: To Clean/Old
  datasetLastDatasetVersion?: { [dataset_id: string]: Models.DatasetVersion };
  datasetsVersion?: { [datasetVersion_id: string]: Models.DatasetVersion };

  showEditName?: boolean;
  showEditDescription?: boolean;
  showUploadDataset?: boolean;
  showCreateFolder?: boolean;
  showEditPermissions?: boolean;

  error?: string;
  selection?: any;

  callbackIntoFolderAction?: Function;
  actionName?: string;

  showInputFolderId?: boolean;
  initFolderId?: string;
  inputFolderIdActionDescription?: string;

  actionIntoFolderValidation?: string;
  actionIntoFolderHelp?: string;

  loading?: boolean;

  // New
  folder?: Models.NamedId;
  name?: string;
  searchEntries?: Array<Models.SearchEntry>;

  searchQuery?: string;
}

export class Conditional extends React.Component<any, any> {
  render() {
    if (this.props.show) {
      return <div>{this.props.children}</div>;
    } else {
      return null;
    }
  }
}

export class SearchView extends React.Component<
  SearchViewProps,
  SearchViewState
> {
  constructor(props: any) {
    super(props);
  }

  private bootstrapTable: any;

  componentDidUpdate(prevProps: SearchViewProps) {}

  componentDidMount() {
    // this.doFetch().then(() => {
    //     this.logAccess();
    // });

    // Get the datasets from query + current_folder
    this.doFetchSearch().then((searchResult: Models.SearchResult) => {
      console.log("Received the search results!");
      console.log("=> " + searchResult);

      this.setState({
        folder: searchResult.current_folder,
        name: searchResult.name,
        searchEntries: searchResult.entries,
      });
    });
  }

  doFetchSearch() {
    // Ask the server about the entries matching the search inside the current_folder
    // Return entries with breadcrumb (list of folders)
    return this.props.tapi.get_folder_search(
      this.props.match.params.currentFolderId,
      this.props.match.params.searchQuery
    );
  }

  // BootstrapTable Entries
  nameUrlFormatter(cell: any, row: BootstrapTableSearchEntry) {
    // TODO: Think about Command Pattern instead of repeating this dangerous check here and in models.ts
    let glyphicon = null;
    if (row.type === Models.FolderEntriesTypeEnum.Folder) {
      glyphicon = <Glyphicon glyph="glyphicon glyphicon-folder-close" />;
    } else if (row.type === Models.FolderEntriesTypeEnum.Dataset) {
      glyphicon = <Glyphicon glyph="glyphicon glyphicon-inbox" />;
    } else if (row.type === Models.FolderEntriesTypeEnum.VirtualDataset) {
      glyphicon = <Glyphicon glyph="glyphicon glyphicon-flash" />;
    } else if (row.type === Models.FolderEntriesTypeEnum.DatasetVersion) {
      glyphicon = <Glyphicon glyph="glyphicon glyphicon-file" />;
    }

    return (
      <span title={cell}>
        {glyphicon}
        <span> </span>
        <Link key={row.id} to={row.url}>
          {cell}
        </Link>
      </span>
    );
  }

  typeFormatter(cell: string, row: BootstrapTableSearchEntry) {
    if (cell) {
      return cell[0].toUpperCase() + cell.slice(1, cell.length);
    } else {
      return "";
    }
  }

  dataFormatter(cell: Date, row: BootstrapTableSearchEntry) {
    return toLocalDateString(cell.toDateString());
  }

  onRowSelect(row: BootstrapTableSearchEntry, isSelected: Boolean, e: any) {
    let select_key = row.id;
    const original_selection: any = this.state.selection;

    let updated_selection: Array<string>;

    let index = original_selection.indexOf(select_key);
    if (index !== -1) {
      updated_selection = _update(original_selection, {
        $splice: [[index, 1]],
      });
    } else {
      updated_selection = _update(original_selection, { $push: [select_key] });
    }

    this.setState({ selection: updated_selection });
  }

  onAllRowsSelect(isSelected: Boolean, rows: Array<BootstrapTableSearchEntry>) {
    const original_selection: any = this.state.selection;
    let updated_selection: Array<string> = original_selection;

    let select_key = null;
    let index = null;
    rows.forEach((row) => {
      select_key = row.id;
      index = updated_selection.indexOf(select_key);

      if (index !== -1) {
        updated_selection = _update(updated_selection, {
          $splice: [[index, 1]],
        });
      } else {
        updated_selection = _update(updated_selection, { $push: [select_key] });
      }
    });

    this.setState({ selection: updated_selection });
  }

  // Search
  executeSearch(searchQuery: any) {
    let url = relativePath(
      "search/" + this.state.folder.id + "/" + searchQuery
    );
    window.location.href = url;
  }

  searchKeyPress(event: any, searchQuery: any) {
    if (event.key === "Enter") {
      this.executeSearch(searchQuery);
    }
  }

  render() {
    let entriesOutput: Array<any> = [];
    let navItems: MenuItem[] = [];
    let folderEntriesTableFormatted: Array<BootstrapTableSearchEntry> = [];

    if (!this.state) {
      return (
        <div>
          <LeftNav items={[]} />
          <div id="main-content" />
        </div>
      );
    } else if (
      this.state.error &&
      this.state.error.toUpperCase() === "NOT FOUND".toUpperCase()
    ) {
      let message =
        "The folder " +
        this.props.match.params.folderId +
        " does not exist. Please check this id " +
        "is correct. We are also available via the feedback button.";
      return (
        <div>
          <LeftNav items={[]} />
          <div id="main-content">
            <NotFound message={message} />
          </div>
        </div>
      );
    } else if (this.state.error) {
      return (
        <div>
          <LeftNav items={[]} />
          <div id="main-content">An error occurred: {this.state.error}</div>
        </div>
      );
    }

    let folder: Models.NamedId = null;
    if (this.state && this.state.folder) {
      folder = this.state.folder;
      folderEntriesTableFormatted = this.state.searchEntries.map(
        (entry: Models.SearchEntry) => {
          return new BootstrapTableSearchEntry(entry);
        }
      );
    }

    // Bootstrap Table configuration
    const check_mode: any = "checkbox";
    const selectRowProp: any = {
      mode: check_mode,
      onSelect: (row: any, isSelected: Boolean, e: any) => {
        this.onRowSelect(row, isSelected, e);
        return true;
      },
      onSelectAll: (
        isSelected: Boolean,
        currentSelectedAndDisplayData: Array<BootstrapTableSearchEntry>
      ) => {
        this.onAllRowsSelect(isSelected, currentSelectedAndDisplayData);
        return true;
      },
    };

    const desc_sortOrder: any = "desc";
    const options: any = {
      noDataText: "Nothing created yet",
      defaultSortName: "creation_date", // default sort column name
      defaultSortOrder: desc_sortOrder, // default sort order
    };

    return (
      <div>
        <LeftNav items={navItems} />
        <div id="main-content">
          {folder && (
            <span>
              <h1>{this.state.name}</h1>

              <Grid
                fluid={true}
                style={{
                  padding: "0px 15px 0px 0px",
                }}
              >
                <Row className="show-grid">
                  <Col md={8}></Col>
                  <Col md={4}>
                    <SearchInput
                      onKeyPress={(event, searchQuery) =>
                        this.searchKeyPress(event, searchQuery)
                      }
                      onClick={(searchQuery) => this.executeSearch(searchQuery)}
                    />
                    <br />
                  </Col>
                </Row>
              </Grid>

              <BootstrapTable
                data={folderEntriesTableFormatted}
                bordered={false}
                tableStyle={tableEntriesStyle}
                ref={(ref: any) => {
                  this.bootstrapTable = ref;
                }}
                options={options}
                striped
                hover
              >
                <TableHeaderColumn dataField="id" isKey hidden>
                  ID
                </TableHeaderColumn>
                <TableHeaderColumn
                  dataField="name"
                  dataSort
                  dataFormat={this.nameUrlFormatter}
                >
                  Name
                </TableHeaderColumn>
                <TableHeaderColumn
                  dataField="creation_date"
                  dataSort
                  dataFormat={this.dataFormatter}
                  width="100"
                >
                  Date
                </TableHeaderColumn>
                <TableHeaderColumn
                  dataField="type"
                  dataFormat={this.typeFormatter}
                  dataSort
                  width="100"
                >
                  Type
                </TableHeaderColumn>
                <TableHeaderColumn
                  dataField="creator_name"
                  dataSort
                  width="150"
                >
                  Creator
                </TableHeaderColumn>
              </BootstrapTable>

              {this.state.loading && <LoadingOverlay></LoadingOverlay>}
            </span>
          )}
        </div>
      </div>
    );
  }
}
