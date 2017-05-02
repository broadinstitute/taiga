import * as React from "react";
import * as ReactDOM from "react-dom";

import { RouteProps, Router, Route, Link, IndexRoute, browserHistory } from 'react-router';

import {FolderView} from "./components/FolderView"
import {DatasetView} from "./components/DatasetView"

import {TaigaApi} from "./models/api"
import {User} from "./models/models"

import {Token} from "./components/Token"
import {RecentlyViewed} from "./components/RecentlyViewed"

import {relativePath} from "./utilities/route"
import {isNullOrUndefined} from "util";
import {Provenance} from "./components/Provenance";

interface AppProps {
    route?: any;
}

const tapi = new TaigaApi(relativePath("api"));

class App extends React.Component<AppProps, any> {
    static childContextTypes = {
        tapi: React.PropTypes.object,
        currentUser: React.PropTypes.string
    };

    constructor(props: any) {
        super(props);
    }

    getChildContext() {
        return {
            tapi: tapi,
            currentUser: this.props.route.user.id
        };
    };

    componentDidMount() {
        // TODO: We should find a way to only get_user once, instead of in Home and in App
    }

    render() {
        // TODO: Get the revision from package.json?
        const trash_link: any = (this.props.route.user &&
            <Link to={relativePath('folder/'+this.props.route.user.trash_folder_id)}
                className="headerTitle">Trash</Link>
        );

        return (
            <div id="main_react">
                <div id="header">
                    <div className="top-page-menu">
                        <img id="taiga_logo"/>
                        {/*TODO: Change the way we manage spaces*/}
                        <span className="headerSpan softwareAppName">Taiga</span>
                        <Link to={relativePath('')} className="headerTitle">Home</Link>
                        <span className="headerSpan"></span>
                        <Link to={relativePath('folder/public')} className="headerTitle">Public</Link>
                        <span className="headerSpan"></span>
                        {trash_link}
                        <span className="headerSpan"></span>
                        <Link className="headerTitle" to={relativePath('recentlyViewed/')}>Recently Viewed</Link>
                    </div>

                    <div className="login-box pull-right">
                        <Link className="tokenLink headerTitle" to={relativePath('token/')}>My Token</Link>
                        {/*TODO: Change this a proper logout behavior*/}
                        {/*<Link className="logoutLink" to={relativePath('')}>Logout</Link>*/}
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
                        Rev 1.4.2
                    </div>
                </footer>
            </div>
        )
    }
}

const Home = React.createClass({
    getInitialState() {
        return {
            user: null
        };
    },

    componentDidMount() {
        let tapi: TaigaApi = this.context.tapi;

        tapi.get_user().then(user => {
                this.setState({user: user}, () => {
                    browserHistory.push(relativePath("folder/" + this.state.user.home_folder_id));
                });
            }
        );
    },

    render() {
        if (isNullOrUndefined(this.state.user)) {
            return <div id="main-content">Loading</div>
        } else {
            return (
                <div id="main-content">
                    <p>
                        <Link to={relativePath("folder/"+this.state.user.home_folder_id)}>My Data</Link>
                    </p>
                </div>
            );
        }
    }
});
Home.contextTypes = {
    tapi: React.PropTypes.object
};


const ActivityView = React.createClass({
    render() {
        var rows: any = [];
        return (
            <table>
                <thead>
                <tr>
                    <th>Date</th>
                    <th>Who</th>
                    <th>Change</th>
                    <th>Comments</th>
                </tr>
                </thead>
                <tbody>
                {rows}
                </tbody>
            </table>
        )
    }
});

const ProvenanceView = React.createClass({
    render() {
        var rows: any = [];
        return (
            <div>
                <h2>This derived from</h2>
                <p>Method: ...</p>
                <table>
                    <thead>
                    <tr>
                        <th>Label</th>
                        <th>Dateset</th>
                        <th>Version</th>
                        <th>Filename</th>
                    </tr>
                    </thead>
                    <tbody>
                    {rows}
                    </tbody>
                </table>

                <h2>Derived from this</h2>
                <table>
                    <thead>
                    <tr>
                        <th>Filenames</th>
                        <th>Dateset</th>
                        <th>Version</th>
                    </tr>
                    </thead>
                    <tbody>
                    {rows}
                    </tbody>
                </table>

            </div>
        )
    }
});


const NoMatch = React.createClass({
    render() {
        return (
            <div>
                No such page
            </div>
        )
    }
});

// TODO: let UserRoute: Component<UserRouteProps, ComponentState> = Route as any

tapi.get_user().then((user: User) => {
    ReactDOM.render((
        <Router history={browserHistory}>
            <Route path={relativePath('')} component={App} user={user}>
                <IndexRoute component={Home}/>
                <Route path="dataset/:datasetId" component={DatasetView as any}/>
                <Route path="dataset/:datasetId/:datasetVersionId" component={DatasetView as any}/>
                <Route path="folder/:folderId" component={FolderView as any}/>
                <Route path="token/" component={ Token as any }/>
                <Route path="recentlyViewed/" component={ RecentlyViewed as any }/>
                <Route path="provenance/:graphId" component={Provenance as any}/>
            </Route>
            <Route path="*" component={NoMatch}/>
        </Router>
    ), document.getElementById('root'));
});
