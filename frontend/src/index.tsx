import * as React from "react";
import * as ReactDOM from "react-dom";

import { Router, Route, Link, IndexRoute, browserHistory } from 'react-router';

import { FolderView } from "./components/FolderView"
import { DatasetView } from "./components/DatasetView"
import { LeftNav } from "./components/LeftNav"
import { TaigaApi } from "./models/api.ts"

const tapi = new TaigaApi("/api");

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
        
        console.log("get_user");
        tapi.get_user().then(user => {
            this.setState({user: user})
            console.log("complete");
            }
        );
    },

    render() {
        if(this.state.user == null) {
            return <div>Loading</div>
        } else {
            return (
                <div>
                    <p>
                        <Link to={"/app/folder/"+this.state.user.home_folder_id}>Home</Link>
                    </p>
                </div>
            );
        }
    }
});
Home.contextTypes = {
    tapi: React.PropTypes.object
};


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

ReactDOM.render((
  <Router history={browserHistory}>
    <Route path="/app" component={App}>
        <IndexRoute component={Home} />
        <Route path="dataset/:datasetVersionId" component={DatasetView as any}>
            <IndexRoute component={DatasetDetails}/>
            <Route path="activity" component={ActivityView}/>
            <Route path="provenance" component={ProvenanceView}/>
        </Route>
        <Route path="folder/:folderId" component={FolderView as any}/>
    </Route>
    <Route path="*" component={NoMatch}/>
  </Router>
), document.getElementById('root'))

