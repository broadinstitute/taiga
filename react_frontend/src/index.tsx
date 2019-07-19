import * as React from "react";
import * as ReactDOM from "react-dom";

import { Route, Redirect, Switch } from "react-router";
import { Link, BrowserRouter } from "react-router-dom";

import { FolderView } from "./components/FolderView";
import { DatasetView } from "./components/DatasetView";
import { SearchView } from "./components/SearchView";

import { TaigaApi } from "./models/api";
import { User } from "./models/models";

import { Token } from "./components/Token";
import { RecentlyViewed } from "./components/RecentlyViewed";

import { GroupListView } from "./components/GroupListView";
import { GroupView } from "./components/GroupView";

import { relativePath } from "./utilities/route";
import { FormControl, Overlay, Popover, Tooltip } from "react-bootstrap";
import { SHA } from "./version"

interface AppProps {
    route?: any;
    tapi: object;
    user: User;
}

interface AppState {
    jumpToValue?: string;
    show?: boolean;
    target?: any;
    message?: string;
}


const tapi = new TaigaApi(relativePath("api"), (window as any).taigaUserToken); // FIXME

class App extends React.Component<AppProps, AppState> {
    constructor(props: any) {
        super(props);

        this.state = {
            jumpToValue: "",
            show: false,
            target: null,
            message: ""
        };
    }


    componentWillMount() {
    }

    componentDidMount() {
        // TODO: We should find a way to only get_user once, instead of in Home and in App
    }

    // TODO: Create a component for jumpTo instead
    jumpToHandleChange(e: any) {
        // if e is enter, then fetch result and change page
        this.setState({
            jumpToValue: e.target.value
        });
    }

    jumpToKeyPress(e: any) {
        if (e.nativeEvent.key === "Enter") {
            let escaped_entry = e.target.value.replace(/\//g, "%2F");
            tapi.get_dataset_version_id(escaped_entry).then((dataset_version_id) => {
                let url = relativePath("/dataset/" +
                    "placeholder" +
                    "/" + dataset_version_id);
                location.replace(url);
            }).catch((reason) => {
                let error_message = undefined;
                // TODO: Find a better way to catch the error properly and not use a string
                if (reason.message === "NOT FOUND") {
                    error_message = [<p>This dataset or dataset version id was not found</p>];
                } else {
                    error_message = [<p>Unknown error: + {reason.message}</p>];
                }

                // Indication of how to use it
                error_message.push(<p>Usage:
                    <br />   - dataset_permaname
                    <br />   - dataset_permaname.version
                    <br />   - dataset_permaname/version
                    <br />
                    <br />   - dataset_id
                    <br />   - dataset_id.version
                    <br />   - dataset_id/version
                    <br />
                    <br />   - dataset_version_id
                </p>);
                // error_message += "</br>  - {dataset_id}.{version}";

                // error_message += "</p>";
                this.setState({
                    show: true,
                    message: error_message
                } as any);
            });
        }
    }

    render() {
        // TODO: Get the revision from package.json?
        const trash_link: any = (this.props.user &&
            <Link to={relativePath("folder/" + this.props.user.trash_folder_id)}
                className="headerTitle">Trash</Link>
        );

        const tooltip = (
            <Tooltip placement="right" className="in">
                Hi
            </Tooltip>
        );

        return (
            <div id="main_react">
                <div id="header">
                    <div className="top-page-menu">
                        <img id="taiga_logo" />
                        {/*TODO: Change the way we manage spaces*/}
                        <span className="headerSpan softwareAppName">Taiga</span>
                        <Link to={relativePath("")} className="headerTitle">Home</Link>
                        <span className="headerSpan"></span>
                        <Link to={relativePath("folder/public")} className="headerTitle">Public</Link>
                        <span className="headerSpan"></span>
                        {trash_link}
                        <span className="headerSpan"></span>
                        <Link className="headerTitle" to={relativePath("recentlyViewed/")}>Recently Viewed</Link>

                        <FormControl
                            ref={(button) => {
                                // FIXME: This is very wrong. State should never be updated like this
                                (this.state as any).target = button;
                            }}
                            type="text"
                            value={this.state.jumpToValue}
                            placeholder="Enter dataset and version (with . or / separator)"
                            onChange={(event) => this.jumpToHandleChange(event)}
                            onKeyPress={(event) => this.jumpToKeyPress(event)}
                            className="headerJumpTo"
                        />

                        <Overlay
                            show={this.state.show}
                            rootClose={true}
                            onHide={() => this.setState({ show: false })}
                            placement="bottom"
                            container={this}
                            target={() => ReactDOM.findDOMNode(this.state.target)}
                        >
                            <Popover>
                                {this.state.message}
                            </Popover>
                        </Overlay>

                    </div>

                    <div className="login-box pull-right">
                        <Link className="tokenLink headerTitle" to={relativePath("token/")}>My Token</Link>
                        {/*TODO: Change this a proper logout behavior*/}
                        {/*<Link className="logoutLink" to={relativePath('')}>Logout</Link>*/}
                        <span className="headerSpan"></span>
                        <Link className="tokenLink headerTitle" to={relativePath("groups/")}>My Groups</Link>
                        <span className="headerSpan"></span>
                        <a href="https://docs.google.com/forms/d/e/1FAIpQLSe_byA04iJsZq9WPqwNfPkEOej8KXg0XVimr6NURMJ_x3ND9w/viewform"
                            target="_blank"
                            className="headerTitle headerTitleMinor">
                            Feedback
                        </a>
                    </div>
                </div>

                <div id="content">
                    <div>{this.props.children}</div>
                </div>

                <footer id="footer">
                    <div className="top-page-menu bottom-page-text">
                        Broad Institute, Cancer Program Data Science {(new Date()).getFullYear()}
                    </div>
                    <div className="login-box pull-right bottom-page-text">
                        <a href="https://github.com/broadinstitute/taiga"
                            target="_blank"
                            className="headerTitle headerTitleMinor">SHA {SHA}</a>
                    </div>
                </footer>
            </div>
        );
    }
}

export interface HomeProps {
    user: User;
}
export class Home extends React.Component<HomeProps, any> {
    constructor(props: any) {
        super(props);
    }

    render() {
        return (
            <Redirect to={relativePath("folder/" + this.props.user.home_folder_id)} />
        );
    }
}



// const ActivityView = React.createClass({
//     render() {
//         let rows: any = [];
//         return (
//             <table>
//                 <thead>
//                     <tr>
//                         <th>Date</th>
//                         <th>Who</th>
//                         <th>Change</th>
//                         <th>Comments</th>
//                     </tr>
//                 </thead>
//                 <tbody>
//                     {rows}
//                 </tbody>
//             </table>
//         );
//     }
// });


export class NoMatch extends React.Component<any, any> {
    render() {
        return (
            <div>
                No such page
            </div>
        );
    }
}

// TODO: let UserRoute: Component<UserRouteProps, ComponentState> = Route as any

export function initPage(element: any) {
    console.log("initPage", tapi);
    console.log("initPage2", tapi);
    tapi.get_user().then((user: User) => {
        console.log("initPage3");
        console.log("in initPage user", user);
        ReactDOM.render(
			<BrowserRouter>
				<App tapi={tapi} user={user}>
					<Route
						path={relativePath("")}
						exact
						render={_ => {
                            return <Home user={user}/>
                        }}
					/>
					<Switch>
						<Route
							path={relativePath(
								"dataset/:datasetId.:datasetVersionId/:fileName"
							)}
							render={props => {
								return (
									<DatasetView
										{...props}
										tapi={tapi}
									/>
								);
							}}
						/>
						<Route
							path={relativePath(
								"dataset/:datasetId/:datasetVersionId"
							)}
							render={props => {
								return (
									<DatasetView
										{...props}
										tapi={tapi}
									/>
								);
							}}
						/>
						<Route
							path={relativePath(
								"dataset/:datasetId.:datasetVersionId"
							)}
							render={props => {
								return (
									<DatasetView
										{...props}
										tapi={tapi}
									/>
								);
							}}
						/>
						<Route
							path={relativePath("dataset/:datasetId")}
							render={props => {
								return (
									<DatasetView
										{...props}
										tapi={tapi}
									/>
								);
							}}
						/>
					</Switch>
					<Route
						path={relativePath(
							"dataset_version/:datasetVersionId"
						)}
						render={props => {
							return (
								<DatasetView {...props} tapi={tapi} />
							);
						}}
					/>
					<Route
						path={relativePath("folder/:folderId")}
						render={props => {
							return (
								<FolderView
									{...props}
									tapi={tapi}
									user={user}
									currentUser={user.id}
								/>
							);
						}}
					/>
					<Route
						path={relativePath(
							"search/:currentFolderId/:searchQuery"
						)}
						render={props => {
							return (
								<SearchView {...props} tapi={tapi} />
							);
						}}
					/>
					<Route
						path={relativePath("token/")}
						render={props => {
							return (
								<Token {...props} tapi={tapi} />
							);
						}}
					/>
					<Route
						path={relativePath("recentlyViewed/")}
						render={props => {
							return (
								<RecentlyViewed {...props} tapi={tapi} />
							);
						}}
					/>
					<Route
						path={relativePath("groups/")}
						render={props => {
							return (
								<GroupListView {...props} tapi={tapi} />
							);
						}}
					/>
					<Route
						path={relativePath("group/:groupId")}
						render={props => {
							return (
								<GroupView {...props} tapi={tapi} />
							);
						}}
					/>
					<Route path="*" component={NoMatch} />
				</App>
			</BrowserRouter>,
			element
		);
    });
}
