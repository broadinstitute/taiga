import * as React from "react";
import { Link } from 'react-router';
import { Button } from "react-bootstrap";

import { LeftNav } from "./LeftNav"

import * as Models from "../models/models"
import { TaigaApi } from "../models/api"

import * as Dialogs from "./Dialogs"
import * as Upload from "./modals/Upload";

import { toLocalDateString } from "../Utilities/formats";
import { relativePath } from "../Utilities/route";

export interface DatasetViewProps {
    params : any
}

export interface DatasetViewState {
    dataset?: Models.Dataset;
    datasetVersion?: Models.DatasetVersion;
    showEditName? : boolean;
    showEditDescription? : boolean;
    showUploadDataset?: boolean;
}

let tapi: TaigaApi = null;

export class DatasetView extends React.Component<DatasetViewProps, DatasetViewState> {
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    componentDidUpdate (prevProps : DatasetViewProps) {
        // respond to parameter change in scenario 3
        let oldId = prevProps.params.datasetVersionId
        let newId = this.props.params.datasetVersionId
        if (newId !== oldId)
            this.doFetch();
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        this.doFetch();
    }

    doFetch() {
        // could do fetches in parallel if url encoded both ids
        return tapi.get_dataset_version_with_dataset(this.props.params.datasetId,
                                                        this.props.params.datasetVersionId
        ).then((datasetAndDatasetVersion: Models.DatasetAndDatasetVersion) => {
            let dataset = datasetAndDatasetVersion.dataset;
            let datasetVersion = datasetAndDatasetVersion.datasetVersion;
            this.setState({
                dataset: dataset, datasetVersion: datasetVersion
            });
        });
    }

    updateName(name : string) {
        tapi.update_dataset_name(this.state.datasetVersion.dataset_id, name).then( () => {
            return this.doFetch()
        } )
    }

    updateDescription(description : string) {
        tapi.update_dataset_description(this.state.datasetVersion.dataset_id, description).then( () => {
            return this.doFetch()
        } )        
    }

    getLinkOrNot(dataset_version: Models.DatasetVersion){
        let dataset = this.state.dataset;
        if(dataset_version.id == this.state.datasetVersion.id){
            return <span>{dataset_version.name}</span>
        }
        else {
            return <Link to={relativePath("dataset/"+dataset.id+"/"+dataset_version.id)}>{dataset_version.name}</Link>
        }
    }

    showUploadNewVersion(e: any) {
        this.setState({
            showUploadDataset: true
        })
    }

    render() {
        if(! this.state) {
           return     <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    Loading...
                </div>
                </div>
        }
        let dataset = this.state.dataset;
        let datasetVersion = this.state.datasetVersion;

        let versions = dataset.versions.map((dataset_version: Models.DatasetVersion, index: any) => {
            return <span key={dataset_version.id} >
                        {this.getLinkOrNot(dataset_version)}
                        {dataset.versions.length != index + 1 &&
                            <span>, </span>
                        }
                    </span>
        });

        let entries = datasetVersion.datafiles.map( (df, index) => {
            return <tr key={index}>
                    <td>{df.name}</td>
                    {/*<td>{df.description}</td>*/}
                    <td>{df.content_summary}</td>
                    <td><a href={df.url} download={true}>{df.type}</a></td>
                </tr>
        });

        let folders = dataset.folders.map( (f, index) => {
            return <Link key={index} to={relativePath("folder/"+f.id)}>{f.name}</Link>
        } )

        let navItems = [
            {label: "Edit Name", action: () => {
                this.setState({ showEditName : true })
            }},
            {label: "Edit Description", action: () => {
                this.setState({ showEditDescription : true })
            }},
            {label: "Add permaname", action: function() {}},
            {label: "Create new version", action: function(){}},
            {label: "Deprecate version", action: function(){}},
            {label: "Show History", action: function(){}}
        ];
 
        let ancestor_section :any = null;
        if(datasetVersion.provenance) {
            let ancestor_dataset_versions = new Set(datasetVersion.provenance.inputs.map( x => {
                return {
                    name: x.dataset_version_name,
                    id: x.dataset_version_id 
                    };
                }))
            let ancestor_links = [...ancestor_dataset_versions].map( (x, index) => {
                return <li key={index}>
                    <Link to={relativePath("dataset/"+x.id)}>{x.name}</Link>
                </li>
            })
            if(ancestor_links.length > 0) {
                ancestor_section =
                    <span>
                        <p>
                            Derived from
                        </p>
                        <ul>
                            {ancestor_links}
                        </ul>
                    </span>;
            } 
        }

        return <div>
            <LeftNav items={navItems}/>
            <div id="main-content">
                <Dialogs.EditName isVisible={this.state.showEditName}
                    initialValue={this.state.dataset.name} 
                    cancel={ () => { this.setState({showEditName: false})} }
                    save={ (name:string) => {
                        this.setState({showEditName: false});
                        this.updateName(name)
                        } } />
                <Dialogs.EditDescription isVisible={this.state.showEditDescription}
                                        cancel={ () => { this.setState({showEditDescription: false})} }
                    initialValue={this.state.dataset.description} 
                    save={ (description:string) => { 
                        this.setState({showEditDescription: false})
                        console.log("Save description: "+description);
                        this.updateDescription(description);
                    } } />

                <Upload.UploadDataset
                        isVisible={this.state.showUploadDataset}
                        cancel={ () => { this.setState({showUploadDataset: false}) } }
                        onFileUploadedAndConverted={ () => {
                            // TODO: Navigate to the new dataset
                            this.doFetch();
                        }}
                        currentFolderId={this.state.dataset.folders[0].id}
                        title="New Dataset Version"
                        readOnlyName={ this.state.dataset.name }
                        readOnlyDescription={ this.state.dataset.description }
                        previousVersionName={ this.state.datasetVersion.name }
                        previousVersionFiles={ this.state.datasetVersion.datafiles }
                    />

                <h1>{dataset.name} <small>{dataset.permanames[dataset.permanames.length-1]}</small></h1>
                <p>Version {datasetVersion.version} created by {datasetVersion.creator.name} on {toLocalDateString(datasetVersion.creation_date)}</p>
                <p>Versions: {versions} </p>

                <Button bsStyle="link" onClick={(e) => this.showUploadNewVersion(e)}>
                    Upload a new version
                </Button>

                <p>Contained within {folders}</p>
                {ancestor_section}

                {Dialogs.renderDescription( this.state.dataset.description )}

                <h2>Contents</h2>
                <table className="table">
                <thead>
                    <tr>
                        <th>Name</th>
                        {/*<th>Description</th>*/}
                        <th>Contains</th>
                        <th>Download</th>
                    </tr>
                </thead>
                <tbody>
                    {entries}
                </tbody>
                </table>
            </div> 
            </div>
        }
    }


