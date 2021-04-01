import React, { useState } from "react";
import { Link } from "react-router-dom";
import { Row, Col, Well, Button, Label, ButtonToolbar } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBell,
  faBellSlash,
  faEdit,
  faExclamationCircle,
  faTimesCircle,
  faUserLock,
} from "@fortawesome/free-solid-svg-icons";

import { renderDescription } from "src/components/Dialogs";
import TextEditable from "src/common/components/TextEditable";
import EditDescriptionModal from "src/common/components/EditDescriptionModal";

import { Dataset, DatasetVersion, StatusEnum, User } from "src/models/models";
import TaigaApi from "src/models/api";

import { toLocalDateString } from "src/utilities/formats";
import { relativePath } from "src/utilities/route";
import { getDatasetPermaname } from "src/utilities/dataset";

export interface Props {
  tapi: TaigaApi;
  user: User;
  dataset: Dataset;
  datasetVersion: DatasetVersion;
  updateDataset: (key: keyof Dataset, value: any) => void;
}

const DatasetMetadataSection = (props: Props) => {
  const { tapi, user, dataset, datasetVersion, updateDataset } = props;
  const [description, setDescription] = useState(datasetVersion.description);
  const [showEditDescriptionModal, setShowEditDescriptionModal] = useState(
    false
  );
  const [changesDescription, setChangesDescription] = useState(
    datasetVersion.changes_description
  );
  const [
    showEditChangesDescriptionModal,
    setShowEditChangesDescriptionModal,
  ] = useState(false);

  const permaname = getDatasetPermaname(dataset);

  const datasetIsInHomeFolder = dataset.folders.some(
    (folder) => folder.id === user.home_folder_id
  );
  return (
    <>
      <Row componentClass="section">
        <Col md={12}>
          <Row>
            <Col md={8}>
              <h1>
                <span className="mr-2">
                  <TextEditable
                    id="dataset-name"
                    title="Edit dataset name"
                    value={dataset.name}
                    placement="right"
                    onConfirm={(newName) => {
                      tapi
                        .update_dataset_name(dataset.id, newName)
                        .then(() => updateDataset("name", newName));
                    }}
                  />
                </span>

                <small className="mr-2 select-text">{permaname}</small>

                {datasetVersion.state === StatusEnum.Deprecated && (
                  <small>
                    <Label bsStyle="warning">
                      <FontAwesomeIcon icon={faExclamationCircle} />
                      <span>Deprecated</span>
                    </Label>
                  </small>
                )}
                {datasetVersion.state === StatusEnum.Deleted && (
                  <small>
                    <Label bsStyle="danger">
                      <FontAwesomeIcon icon={faTimesCircle} />
                      <span>Deleted</span>
                    </Label>
                  </small>
                )}
              </h1>
            </Col>

            <Col md={4}>
              <ButtonToolbar>
                {dataset.subscription_id ? (
                  <Button
                    bsSize="xs"
                    onClick={() =>
                      tapi
                        .delete_subscription(dataset.subscription_id)
                        .then(() => updateDataset("subscription_id", null))
                    }
                  >
                    <FontAwesomeIcon icon={faBellSlash} />
                    <span>Unsubscribe</span>
                  </Button>
                ) : (
                  <Button
                    bsSize="xs"
                    onClick={() =>
                      tapi
                        .add_subscription(dataset.id)
                        .then((r) => updateDataset("subscription_id", r))
                    }
                  >
                    <FontAwesomeIcon icon={faBell} />
                    <span>Subscribe</span>
                  </Button>
                )}
                <Button bsSize="xs">
                  <FontAwesomeIcon icon={faUserLock} />
                  <span>Edit permissions</span>
                </Button>
              </ButtonToolbar>
            </Col>
          </Row>

          <Row>
            <Col md={8}>
              <span>
                Version {datasetVersion.version} created by{" "}
                {datasetVersion.creator.name} on{" "}
                {toLocalDateString(datasetVersion.creation_date)}
              </span>
            </Col>
            <Col md={4}>
              {datasetVersion.state === StatusEnum.Approved && (
                <Button bsSize="xs">Deprecate this version</Button>
              )}
              {datasetVersion.state === StatusEnum.Deprecated && (
                <>
                  <Button bsSize="xs">De-deprecate this version</Button>
                  <Button bsSize="xs">Delete this version</Button>
                </>
              )}
            </Col>
          </Row>
          <Row>
            <Col md={8}>
              <div>
                Versions:{" "}
                {dataset.versions.map((dv, index) => {
                  if (dv.id === datasetVersion.id) {
                    return (
                      <React.Fragment key={dv.id}>
                        {index + 1}
                        {dataset.versions.length !== index + 1 && ", "}
                      </React.Fragment>
                    );
                  }
                  const url = relativePath(`/dataset/${permaname}/${dv.name}`);

                  return (
                    <React.Fragment key={dv.id}>
                      <Link to={url}>{dv.name}</Link>

                      {dataset.versions.length !== index + 1 && ", "}
                    </React.Fragment>
                  );
                })}
              </div>
            </Col>
            <Col md={4}>
              <ButtonToolbar>
                <Button bsSize="xs">Create new version</Button>
              </ButtonToolbar>
            </Col>
          </Row>
          <Row>
            <Col md={8}>
              {dataset.folders.length > 0 && (
                <div>
                  Contained within{" "}
                  {dataset.folders.map((f, index) => {
                    return (
                      <span key={f.id}>
                        <Link to={relativePath(`folder/${f.id}`)}>
                          {f.name}
                        </Link>
                        {dataset.folders.length !== index + 1 && ", "}
                      </span>
                    );
                  })}
                </div>
              )}
            </Col>
            <Col md={4}>
              <ButtonToolbar>
                <Button
                  bsSize="xs"
                  disabled={datasetIsInHomeFolder}
                  onClick={() =>
                    tapi.copy_to_folder([dataset.id], user.home_folder_id)
                  }
                >
                  Add to Home
                </Button>
                <Button bsSize="xs">Add to other folder</Button>
              </ButtonToolbar>
            </Col>
          </Row>

          {datasetVersion.state === StatusEnum.Deprecated && (
            <Well bsSize="sm">
              <i>Deprecation reason:</i>
              <br />
              <span>{datasetVersion.reason_state}</span>
            </Well>
          )}

          <h3 className="h5 mb-1">
            <span className="mr-2">Description</span>
            <Button
              bsSize="xs"
              onClick={() => setShowEditDescriptionModal(true)}
            >
              <FontAwesomeIcon icon={faEdit} />
            </Button>
          </h3>
          {description ? (
            renderDescription(description)
          ) : (
            <div>No description</div>
          )}

          <h3 className="h5 mb-1">
            <span className="mr-2">Changes this version</span>
            <Button
              bsSize="xs"
              onClick={() => setShowEditChangesDescriptionModal(true)}
            >
              <FontAwesomeIcon icon={faEdit} />
            </Button>
          </h3>
          {changesDescription ? (
            <>{renderDescription(changesDescription)}</>
          ) : (
            <div>No description of changes</div>
          )}
        </Col>
      </Row>
      <EditDescriptionModal
        show={showEditDescriptionModal}
        initialDescription={description}
        onSave={(newDescription) => {
          tapi
            .update_dataset_version_description(
              datasetVersion.id,
              newDescription
            )
            .then(() => {
              setDescription(newDescription);
            });
        }}
        onClose={() => setShowEditDescriptionModal(false)}
      />
      <EditDescriptionModal
        show={showEditChangesDescriptionModal}
        initialDescription={changesDescription}
        onSave={(newChangesDescription) => {
          tapi
            .update_dataset_version_changes_description(
              datasetVersion.id,
              newChangesDescription
            )
            .then(() => {
              setChangesDescription(newChangesDescription);
            });
        }}
        onClose={() => setShowEditChangesDescriptionModal(false)}
      />
    </>
  );
};

export default DatasetMetadataSection;
