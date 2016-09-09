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
            return <div>Loading...</div>
        }
        let dataset = this.state.dataset;
        let datasetVersion = this.state.datasetVersion;

        let versions = dataset.versions.map( x => x.name+" ("+x.status+") " ).join(", ");

        let entries = datasetVersion.datafiles.map( df => {
            return <tr>
                    <td>{df.name}</td>
                    <td>{df.mimeType}</td>
                    <td>{df.description}</td>
                    <td>2000 x 15 table</td>
                    <td>123 kb</td>
                </tr>
        });

        let folders = datasetVersion.folders.map( f => {
            return <Link to={"/app/folder/"+f.id}>{f.name}</Link>
        } )

        return <div>
            <h1><button>Edit</button>{dataset.name}</h1>
            <p>Created by: {datasetVersion.creator.name} on {datasetVersion.creation_date}</p>
            <p>Versions: {versions} </p>
            <h2><button>Edit</button>Description</h2>
            <p>Contained within {folders}</p>
            <table className="table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Mime type</th>
                    <th>Description</th>
                    <th>Size</th>
                    <th>Bytes</th>
                </tr>
            </thead>
            <tbody>
                {entries}
            </tbody>
            </table> 
            </div>
        }
    }


