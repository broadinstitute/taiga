import * as React from "react";
import { useState, useRef } from "react";
import * as ReactDOM from "react-dom";

import { Route, Redirect, Switch } from "react-router";
import { BrowserRouter } from "react-router-dom";

import DatasetViewWrapper from "src/dataset/components/DatasetViewWrapper";
import {
  FormGroup,
  FormControl,
  FormControlProps,
  Nav,
  Navbar,
  NavItem,
  Overlay,
  Popover,
} from "react-bootstrap";
import HTMLResponseError from "src/common/models/HTMLReponseError";
import { FolderView } from "./components/FolderView";
import { SearchView } from "./components/SearchView";

import TaigaApi from "./models/api";
import { User } from "./models/models";

import { Token } from "./components/Token";
import { RecentlyViewed } from "./components/RecentlyViewed";

import { GroupListView } from "./components/GroupListView";
import { GroupView } from "./components/GroupView";

import { relativePath } from "./utilities/route";
import { SHA } from "./version";

import "src/common/styles/base.css";

interface GlobalSearchProps {
  tapi: TaigaApi;
}

const GlobalSearch = (props: GlobalSearchProps) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [showTooltip, setShowTooltip] = useState(false);
  const [message, setMessage] = useState("");
  const target = useRef();

  const { tapi } = props;

  const handleSearch = (
    e: React.KeyboardEvent<FormControl & FormControlProps>
  ) => {
    if (e.nativeEvent.key !== "Enter" || searchQuery.length === 0) {
      return;
    }
    const escapedQuery = searchQuery.replace(/\//g, "%2F");
    tapi
      .get_dataset_version_id(escapedQuery)
      .then((dataset_version_id) => {
        const url = relativePath(`/dataset/placeholder/${dataset_version_id}`);
        window.location.replace(url);
      })
      .catch((reason) => {
        if (reason instanceof HTMLResponseError && reason.status === 404) {
          setMessage("This dataset or dataset version id was not found");
        } else {
          setMessage(`Unknown error: ${reason.message}`);
        }
        setShowTooltip(true);
      });
  };

  return (
    <>
      <FormGroup>
        <FormControl
          ref={target}
          type="text"
          value={searchQuery}
          placeholder="Enter dataset and version (with . or / separator)"
          onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
            setSearchQuery(e.currentTarget.value as string)
          }
          onKeyPress={handleSearch}
        />
      </FormGroup>

      <Overlay
        show={showTooltip}
        rootClose
        onHide={() => setShowTooltip(false)}
        placement="bottom"
        target={target.current}
      >
        <Popover id="global-search-help-message">
          <p>{message}</p>
          <br />
          <p>
            Usage:
            <ul>
              <li>dataset_permaname</li>
              <li>dataset_permaname.version</li>
              <li>dataset_permaname/version</li>
            </ul>
            <ul>
              <li>dataset_id</li>
              <li>dataset_id.version</li>
              <li>dataset_id/version</li>
            </ul>
            <ul>
              <li>dataset_version_id</li>
            </ul>
          </p>
        </Popover>
      </Overlay>
    </>
  );
};
interface AppProps {
  tapi: TaigaApi;
  user: User;
  showGroupLink: boolean;
  logoSrc: string;
}

const App = (props: React.PropsWithChildren<AppProps>) => {
  const { user, tapi, showGroupLink, logoSrc, children } = props;
  // TODO: Get the revision from package.json?
  return (
    <>
      <Navbar id="global-nav" fixedTop fluid inverse>
        <Navbar.Header>
          <Navbar.Brand>
            <img id="taiga-logo" src={logoSrc} alt="" />
            <span id="taiga-brand-name">Taiga</span>
          </Navbar.Brand>
          <Navbar.Toggle />
        </Navbar.Header>
        <Navbar.Collapse>
          <Nav>
            <NavItem href={relativePath("")}>Home</NavItem>
            <NavItem href={relativePath("folder/public")}>Public</NavItem>
            <NavItem href={relativePath(`folder/${user.trash_folder_id}`)}>
              Trash
            </NavItem>
            <NavItem href={relativePath("recentlyViewed/")}>Recent</NavItem>
          </Nav>
          <Nav>
            <Navbar.Form>
              <GlobalSearch tapi={tapi} />
            </Navbar.Form>
          </Nav>
          <Nav pullRight>
            <NavItem href={relativePath("token/")}>Account</NavItem>
            {/* TODO: Change this a proper logout behavior */}
            {/* <Link className="logoutLink" to={relativePath('')}>Logout</Link> */}

            {/* {showGroupLink && (
              <NavItem href={relativePath("groups/")}>Groups</NavItem>
            )} */}
            <NavItem
              href="https://docs.google.com/forms/d/e/1FAIpQLSe_byA04iJsZq9WPqwNfPkEOej8KXg0XVimr6NURMJ_x3ND9w/viewform"
              target="_blank"
              rel="noreferrer"
            >
              Feedback
            </NavItem>
          </Nav>
        </Navbar.Collapse>
      </Navbar>

      <main>{children}</main>

      <Navbar id="global-footer" fixedBottom fluid inverse>
        <Nav>
          <Navbar.Text>
            Broad Institute, Cancer Program Data Science{" "}
            {new Date().getFullYear()}
          </Navbar.Text>
        </Nav>
        <Nav pullRight>
          <NavItem
            href="https://github.com/broadinstitute/taiga"
            target="_blank"
            rel="noreferrer"
          >
            SHA {SHA}
          </NavItem>
        </Nav>
      </Navbar>
    </>
  );
};

// eslint-disable-next-line import/prefer-default-export
export function initPage(element: any, logoSrc: string) {
  const tapi = new TaigaApi(
    relativePath("api"),
    (window as any).taigaUserToken
  ); // FIXME

  Promise.all([tapi.get_user(), tapi.get_all_groups_for_current_user()]).then(
    ([user, groups]) => {
      ReactDOM.render(
        <BrowserRouter>
          <App
            tapi={tapi}
            user={user}
            showGroupLink={groups.length > 0}
            logoSrc={logoSrc}
          >
            <Switch>
              <Redirect
                from={relativePath("")}
                exact
                to={relativePath(`folder/${user.home_folder_id}`)}
              />
              <Route
                path={relativePath(
                  "dataset/:datasetId.:datasetVersionId/:fileName"
                )}
                render={(props) => {
                  const { datasetId, datasetVersionId } = props.match.params;
                  return (
                    <Redirect
                      to={relativePath(
                        `dataset/${datasetId}/${datasetVersionId}`
                      )}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("dataset/:datasetId/:datasetVersionId")}
                render={(props) => {
                  const { datasetId, datasetVersionId } = props.match.params;

                  return (
                    <DatasetViewWrapper
                      key={`dataset/${datasetId}/${datasetVersionId}`}
                      tapi={tapi}
                      user={user}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("dataset/:datasetId.:datasetVersionId")}
                render={(props) => {
                  const { datasetId, datasetVersionId } = props.match.params;
                  return (
                    <Redirect
                      to={relativePath(
                        `dataset/${datasetId}/${datasetVersionId}`
                      )}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("dataset/:datasetId")}
                render={(props) => {
                  const { datasetId } = props.match.params;

                  return (
                    <DatasetViewWrapper
                      key={`dataset/${datasetId}`}
                      tapi={tapi}
                      user={user}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("dataset_version/:datasetVersionId")}
                render={(props) => {
                  const { datasetVersionId } = props.match.params;

                  return (
                    <DatasetViewWrapper
                      key={`dataset_version/${datasetVersionId}`}
                      tapi={tapi}
                      user={user}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("folder/:folderId")}
                render={(props) => {
                  return (
                    <FolderView
                      tapi={tapi}
                      user={user}
                      currentUser={user.id}
                      match={props.match}
                      history={props.history}
                      location={props.location}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("search/:currentFolderId/:searchQuery")}
                render={(props) => {
                  return (
                    <SearchView
                      tapi={tapi}
                      match={props.match}
                      history={props.history}
                      location={props.location}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("token/")}
                render={(props) => {
                  return (
                    <Token
                      tapi={tapi}
                      match={props.match}
                      history={props.history}
                      location={props.location}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("recentlyViewed/")}
                render={(props) => {
                  return (
                    <RecentlyViewed
                      tapi={tapi}
                      match={props.match}
                      history={props.history}
                      location={props.location}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("groups/")}
                render={(props) => {
                  return (
                    <GroupListView
                      tapi={tapi}
                      groups={groups}
                      match={props.match}
                      history={props.history}
                      location={props.location}
                    />
                  );
                }}
              />
              <Route
                path={relativePath("group/:groupId")}
                render={(props) => {
                  return (
                    <GroupView
                      tapi={tapi}
                      match={props.match}
                      history={props.history}
                      location={props.location}
                    />
                  );
                }}
              />
              <Route path="*" render={() => <div>No such page</div>} />
            </Switch>
          </App>
        </BrowserRouter>,
        element
      );
    }
  );
}
