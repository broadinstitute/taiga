import * as React from "react";
import * as ReactDOM from "react-dom";

import { Router, Route, Link, IndexRoute, browserHistory } from 'react-router';

import { FolderView } from "./components/FolderView"
import { DatasetView } from "./components/DatasetView"
import { LeftNav } from "./components/LeftNav"
import { TaigaApi } from "./models/api"

import { relativePath } from "./Utilities/route"

const tapi = new TaigaApi(relativePath("api"));

const App = React.createClass({
    getChildContext() {
        return {tapi: tapi};
    },
    
    render() {
        return <div>{this.props.children}</div>
    }
});
App.childContextTypes = {
    tapi: React.PropTypes.object
};

const Home = React.createClass({
    getInitialState() {
        console.log("getInitialState");
        console.log("getInitialState2");
        return {
            user: null
        };
    },

    componentDidMount() {
        let tapi : TaigaApi = this.context.tapi;

        console.log("get_user start in React");
        tapi.get_user().then(user => {
            this.setState({user: user})
            console.log("get_user complete, complete");
            }
        );
    },

    render() {
        if(this.state.user == null) {
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
        var rows : any = [];
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
        var rows : any = [];
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
})


// tapi.get_user().then(user => {
//     console.log("User:", user);
//     return tapi.get_folder(user.home_folder_id)
// }).then(folder => {
//     console.log("Folder:", folder);
// })

            // <IndexRoute component={DatasetDetails}/>
            // <Route path="activity" component={ActivityView}/>
            // <Route path="provenance" component={ProvenanceView}/>


ReactDOM.render((
  <Router history={browserHistory}>
    <Route path={relativePath('')} component={App}>
        <IndexRoute component={Home} />
        <Route path="dataset/:datasetId" component={DatasetView as any}/>
        <Route path="dataset/:datasetId/:datasetVersionId" component={DatasetView as any}/>
        <Route path="folder/:folderId" component={FolderView as any}/>
    </Route>
    <Route path="*" component={NoMatch}/>
  </Router>
), document.getElementById('root'))

