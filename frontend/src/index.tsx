import * as React from "react";
import * as ReactDOM from "react-dom";

import { Router, Route, Link, IndexRoute, browserHistory } from 'react-router';

import { FolderView } from "./components/FolderView"
import { LeftNav } from "./components/LeftNav"

const App = React.createClass({
    render() {
        return <div>{this.props.children}</div>
    }
});

const Home = React.createClass({
    render() {
    return (
        <div>
        <p>
        <Link to="/app/folder/1">folder</Link>
        </p><p>
        <Link to="/app/dataset/2">dataset</Link>
        </p>
        </div>
        )
    }
});

const DatasetView = React.createClass({
    render() {
    return (
        <div>
            <h2>Dataset: {this.props.params.datasetId}</h2>
            <DatasetDetails/>
        </div>
        )
    }
});


const DataFileTable = React.createClass({
    render() {
        var rows : any = [];
        return (
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Summary</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            )
        }
    });

const EditButton = React.createClass({
    render() {
    return (
        <div>
            Edit
        </div>
        )
    }
});

const DatasetDetails = React.createClass({
    render() {
    return (
        <div>
            <LeftNav/>
            <h1>Name</h1><EditButton/>
            Created by, Created time
            Versions...
            Description<EditButton/>
            <DataFileTable/>
        </div>
        )
    }
});

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

ReactDOM.render((
  <Router history={browserHistory}>
    <Route path="/app" component={App}>
        <IndexRoute component={Home}/>
        <Route path="dataset/:datasetId" component={DatasetView}>
            <IndexRoute component={DatasetDetails}/>
            <Route path="activity" component={ActivityView}/>
            <Route path="provenance" component={ProvenanceView}/>
        </Route>
        <Route path="folder/:folderId" component={FolderView}/>
    </Route>
    <Route path="*" component={NoMatch}/>
  </Router>
), document.getElementById('root'))

