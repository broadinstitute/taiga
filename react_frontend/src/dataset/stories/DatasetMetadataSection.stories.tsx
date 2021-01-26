// import * as React from "react";
// import { Story, Meta } from "@storybook/react/types-6-0";

// import DatasetMetadataSection, {
//   Props,
// } from "src/dataset/components/DatasetMetadataSection";
// import {
//   Dataset,
//   DatasetVersion,
//   FolderEntriesTypeEnum,
//   StatusEnum,
// } from "src/models/models";
// export default {
//   title: "DatasetView/DatasetMetadataSection",
//   component: DatasetMetadataSection,
// } as Meta;

// const Template: Story<Props> = (args) => <DatasetMetadataSection {...args} />;
// const defaultDataset: Dataset = {
//   can_edit: true,
//   can_view: true,
//   description: "",
//   folders: [{ id: "folder-id", name: "Home" }],
//   id: "dataset-id",
//   name: "origin",
//   permanames: ["origin-37cb"],
//   subscription_id: "subscription-id",
//   versions: [
//     { id: "dataset-version-id-1", name: "1", status: StatusEnum.Approved },
//     { id: "dataset-version-id-2", name: "2", status: StatusEnum.Approved },
//     { id: "dataset-version-id-3", name: "3", status: StatusEnum.Approved },
//     { id: "dataset-version-id-4", name: "4", status: StatusEnum.Approved },
//   ],
//   type: FolderEntriesTypeEnum.Dataset,
//   creation_date: "2020-01-01",
//   creator: { name: "creator name", id: "creator-id" },
//   acl: null,
// };
// const defaultDatasetVersion: DatasetVersion = {
//   dataset_id: "dataset-1",
//   id: "dataset-version-id-3",
//   dataset: defaultDataset,
//   state: StatusEnum.Approved,
//   reason_state: null,
//   version: "3",
//   name: "3",
//   description: "dataset version description",
//   changes_description: "changes description",
//   datafiles: [],
//   folders: [{ id: "folder-id", name: "Home" }],
//   can_edit: true,
//   can_view: true,
//   creation_date: "2020-01-01",
//   creator: { name: "creator name", id: "creator-id" },
//   figshare: null,
// };

// export const Default = Template.bind({});
// Default.args = {
//   dataset: defaultDataset,
//   datasetVersion: defaultDatasetVersion,
// } as Props;

// export const Deprecated = Template.bind({});
// Deprecated.args = {
//   dataset: defaultDataset,
//   datasetVersion: defaultDatasetVersion,
// } as Props;

// export const Deleted = Template.bind({});
// Deleted.args = {
//   dataset: defaultDataset,
//   datasetVersion: defaultDatasetVersion,
// } as Props;
