import * as React from "react";

import { LeftNav } from "./LeftNav"

import { Link } from 'react-router';

import * as Models from "../models/models"
import { TaigaApi } from "../models/api.ts"

export interface DatasetViewProps {
    params : any
}

export interface DatasetViewState {
    dataset: Models.Dataset;
    datasetVersion: Models.DatasetVersion;
}

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
        this.doFetch();
    }

    doFetch() {
        // could do fetches in parallel if url encoded both ids
        let tapi : TaigaApi = (this.context as any).tapi;
        let _datasetVersion : Models.DatasetVersion = null;

        tapi.get_dataset_version(this.props.params.datasetVersionId).then(datasetVersion => {
            _datasetVersion = datasetVersion;
            return tapi.get_dataset(datasetVersion.dataset_id);
        }).then(dataset => {
            this.setState({dataset: dataset, datasetVersion: _datasetVersion})
        });
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

        let versions = dataset.versions.map( x => x.name+" ("+x.status+") " ).join(", ");

        let entries = datasetVersion.datafiles.map( df => {
            return <tr>
                    <td>{df.name}</td>
                    <td>{df.description}</td>
                    <td>{df.content_summary}</td>
                </tr>
        });

        let folders = datasetVersion.folders.map( f => {
            return <Link to={"/app/folder/"+f.id}>{f.name}</Link>
        } )

        let navItems = [
            {label: "Edit Name", action: function(){} },
            {label: "Edit Description", action: function(){} },
            {label: "Add permaname", action: function() {} },
            {label: "Create new version", action: function(){} },
            {label: "Deprecate version", action: function(){} },
            {label: "Show History", action: function(){} }
        ];
 
        let ancestor_section :any = null;
        if(datasetVersion.provenance) {
            let ancestor_dataset_versions = new Set(datasetVersion.provenance.inputs.map( x => {
                return {
                    name: x.dataset_version_name,
                    id: x.dataset_version_id 
                    };
                }))
            let ancestor_links = [...ancestor_dataset_versions].map( x => {
                return <li>
                    <Link to={"/app/dataset/"+x.id}>{x.name}</Link>
                </li>
            })
            if(ancestor_links.length > 0) {
                ancestor_section = <p>
                    <p>
                        Derived from <ul>{ancestor_links}</ul>
                    </p>
                </p>;
            } 
        }
        return <div>
            <LeftNav items={navItems}/>
            <div id="main-content">
                <h1>{dataset.name} <small>{dataset.permanames[dataset.permanames.length-1]}</small></h1>
                <p>Version {datasetVersion.version} created by {datasetVersion.creator.name} on {datasetVersion.creation_date}</p>
                <p>Versions: {versions} </p>
                <p>Contained within {folders}</p>
                {ancestor_section}
                <h2>Contents</h2>
                <table className="table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Description</th>
                        <th>Contains</th>
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


