import * as React from "react";
import * as Modal from "react-modal";
import * as Showdown from "showdown";

import {
  ControlLabel,
  FormControl,
  FormGroup,
  HelpBlock,
  Button,
} from "react-bootstrap";
import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";

import { isUndefined } from "util";
import { isNullOrUndefined } from "util";
import { relativePath } from "../utilities/route";
import {
  Dataset,
  Entry,
  Folder,
  FolderEntries,
  Group,
  User,
} from "../models/models";
import update from "immutability-helper";

interface InputFolderIdProps extends DialogProps {
  cancel: () => void;
  save: (folderId: string) => void;
  actionDescription: string;

  validationState?: "success" | "warning" | "error";
  help?: string;

  initFolderId?: string;
}

interface InputFolderIdState extends DialogState {
  folderId: string;
}

interface CreateFolderProps extends DialogProps {
  save: (name: string, description: string) => void;
}

interface EditStringProps {
  isVisible: boolean;
  initialValue: string;
  cancel: () => void;
  save: (name: string) => void;
}

export interface DialogProps {
  isVisible: boolean;
  cancel: () => void;
}

export interface DialogState {}

// Don't forget to modify modalStyles in Upload.tsx if you change the code of modalStyles
export const modalStyles: any = {
  content: {
    background: null,
    border: null,
  },
};

export function formSubmitSave(
  reactComponent: React.Component<any, any>,
  event: any,
  argOne: any,
  argTwo: any
) {
  event.preventDefault();
  if (isNullOrUndefined(argTwo)) {
    reactComponent.props.save(argOne);
  } else {
    reactComponent.props.save(argOne, argTwo);
  }
}

export class EditName extends React.Component<EditStringProps, any> {
  textInput: any;

  render() {
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="EditName"
      >
        <form>
          <div className="modal-content">
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="nameInput">Name</label>
                <input
                  type="text"
                  defaultValue={this.props.initialValue}
                  className="form-control"
                  id="nameInput"
                  ref={(c) => {
                    this.textInput = c;
                  }}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-default"
                onClick={this.props.cancel}
              >
                Close
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                onClick={(e) => {
                  formSubmitSave(this, e, this.textInput.value, null);
                }}
              >
                Save changes
              </button>
            </div>
          </div>
        </form>
      </Modal>
    );
  }
}

export class EditDescription extends React.Component<EditStringProps, any> {
  textArea: any;

  render() {
    //className="Modal__Bootstrap modal-dialog"
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="EditDescription"
      >
        <form>
          <div className="modal-content">
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="descriptionInput">Description</label>
                <p>
                  <em>
                    Markdown is accepted.{" "}
                    <a
                      href="http://markdown-guide.readthedocs.io/en/latest/basics.html"
                      target="_blank"
                    >
                      Click here{" "}
                    </a>
                    if you want to have more information about it
                  </em>
                </p>
                <textarea
                  rows={15}
                  defaultValue={this.props.initialValue}
                  className="form-control"
                  id="descriptionInput"
                  ref={(c) => {
                    this.textArea = c;
                  }}
                ></textarea>
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-default"
                onClick={this.props.cancel}
              >
                Close
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                onClick={(e) => {
                  formSubmitSave(this, e, this.textArea.value, null);
                }}
              >
                Save changes
              </button>
            </div>
          </div>
        </form>
      </Modal>
    );
  }
}

export class CreateFolder extends React.Component<CreateFolderProps, any> {
  textInput: any;
  textArea: any;

  render() {
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="CreateFolder"
      >
        <form>
          <div className="modal-content">
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="nameInput">Name</label>
                <input
                  type="text"
                  placeholder="A name is required"
                  className="form-control"
                  id="nameInput"
                  ref={(c) => {
                    this.textInput = c;
                  }}
                />

                <label htmlFor="descriptionInput">Description</label>
                <textarea
                  rows={15}
                  placeholder="No description given"
                  className="form-control"
                  id="descriptionInput"
                  ref={(c) => {
                    this.textArea = c;
                  }}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-default"
                onClick={this.props.cancel}
              >
                Close
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                onClick={(e) => {
                  formSubmitSave(
                    this,
                    e,
                    this.textInput.value,
                    this.textArea.value
                  );
                }}
              >
                Save changes
              </button>
            </div>
          </div>
        </form>
      </Modal>
    );
  }
}

let converter = new Showdown.Converter();

export function renderDescription(description: string) {
  let description_section: any = null;

  if (description) {
    let desc_as_html = { __html: converter.makeHtml(description) };
    description_section = (
      <div className="well well-sm" dangerouslySetInnerHTML={desc_as_html} />
    );
  }

  return description_section;
}

export class InputFolderId extends React.Component<
  InputFolderIdProps,
  InputFolderIdState
> {
  constructor(props: InputFolderIdProps) {
    super(props);
  }

  componentWillMount() {
    this.setState({
      folderId: this.props.initFolderId,
    });
  }

  componentWillReceiveProps(nextProps: any) {
    // When we open the component, we reset it
    this.setState({
      folderId: nextProps.initFolderId,
    });
    // if (nextProps.isVisible && this.props.isVisible != nextProps.isVisible) {
    //
    // }
  }

  handleChange(e: any) {
    this.setState({
      folderId: e.target.value,
    });
  }

  render() {
    let textPlaceHolder =
      "Enter here the id of the folder to " + this.props.actionDescription;

    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="InputFolderId"
      >
        <div className="modal-content">
          <div className="modal-header">
            <h2>{this.props.actionDescription}</h2>
            <p>
              Pleaser enter below the id of the folder. It can be found by going
              into the folder page, and getting the string after '/folder/'.
              E.G.: `cds.team/taiga/folder/<i>hash_id</i>`
            </p>
          </div>
          <form>
            <div className="modal-body">
              <FormGroup validationState={this.props.validationState}>
                <ControlLabel>Folder ID</ControlLabel>
                <FormControl
                  type="text"
                  value={this.state.folderId}
                  placeholder={textPlaceHolder}
                  onChange={(e) => this.handleChange(e)}
                />
                {this.props.help && <HelpBlock>{this.props.help}</HelpBlock>}
              </FormGroup>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-default"
                onClick={() => this.props.cancel()}
              >
                Close
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={(e) => {
                  formSubmitSave(this, e, this.state.folderId, null);
                }}
              >
                Save changes
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }
}

const exportErrorStyle: any = {
  overlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(255, 255, 255, 0.75)",
  },
  content: {
    position: "absolute",
    top: "40px",
    left: "40px",
    right: "40px",
    bottom: "40px",
    border: "1px solid #ccc",
    background: "#fff",
    overflow: "auto",
    WebkitOverflowScrolling: "touch",
    borderRadius: "4px",
    outline: "none",
    padding: "20px",
  },
};

// region Export Error section
export interface ExportErrorProps extends DialogProps {
  isVisible: boolean;
  cancel: () => void;
  retry: () => void;
  message: string;
}

export interface ExportErrorState extends DialogState {}

export class ExportError extends React.Component<
  ExportErrorProps,
  ExportErrorState
> {
  render() {
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="ExportError"
      >
        <div className="modal-content">
          <div className="modal-header">
            <h2 ref="subtitle">Error when exporting</h2>
          </div>
          <form>
            <div className="modal-body">{this.props.message}</div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-default"
                onClick={this.props.cancel}
              >
                Close
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={this.props.retry}
              >
                Retry
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }
}
// endregion

// region Deprecation
export interface DeprecationReasonProps extends DialogProps {
  isVisible: boolean;
  cancel: () => void;
  save: (reason: string) => void;
}

export interface DeprecationReasonState extends DialogState {
  reason: string;
}

export class DeprecationReason extends React.Component<
  DeprecationReasonProps,
  DeprecationReasonState
> {
  constructor(props: DeprecationReasonProps) {
    super(props);
    this.state = { reason: "" };
  }

  componentDidUpdate(prevProps: DeprecationReasonProps) {
    if (this.props.isVisible !== prevProps.isVisible) {
      this.setState({ reason: "" });
    }
  }

  save() {
    this.props.save(this.state.reason);
  }

  handleChange(e: any) {
    this.setState({ reason: e.target.value });
  }

  render() {
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="Deprecation Reason"
      >
        <div className="modal-content">
          <div className="modal-header">
            <h2 ref="subtitle">Reason to deprecate this dataset version</h2>
          </div>
          <form>
            <div className="modal-body">
              <input
                type="text"
                placeholder="Reason for deprecation"
                className="form-control"
                value={this.state.reason}
                onChange={(e) => this.handleChange(e)}
              />
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-default"
                onClick={this.props.cancel}
              >
                Close
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={(e) => this.save()}
              >
                Save changes
              </button>
            </div>
          </form>
        </div>
      </Modal>
    );
  }
}
// endregion

// region Sharing
export interface ShareEntriesProps extends DialogProps {
  entries: Array<Entry>;
}

export interface ShareEntriesState extends DialogState {}

export class ShareEntries extends React.Component<
  ShareEntriesProps,
  ShareEntriesState
> {
  render() {
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="Share entries"
      >
        <div className="modal-content">
          <div className="modal-header">
            <h2 ref="subtitle">Sharing urls</h2>
            <p>Share easily these urls with your collaborators</p>
          </div>
          <div className="modal-body">
            {this.props.entries.map((entry: Entry) => {
              // TODO: Could add the relativePath as a function of an entry in models.ts
              let entryUrl = entry.getFullUrl();

              return (
                <p key={entry.id}>
                  {entry.getName()}:{" "}
                  <a href={entryUrl} target="_blank">
                    {entryUrl}
                  </a>
                </p>
              );
            })}
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-default"
              onClick={this.props.cancel}
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    );
  }
}

export interface AddUsersToGroupProps extends DialogProps {
  group: Group;
  allUsers: Array<User>;
  addUsersToGroup: (userIds: Array<string>) => void;
}

export interface AddUsersToGroupState extends DialogState {
  selection: ReadonlyArray<string>;
}

type BootstrapTableButtonGroup = {
  exportCSVBtn: any;
  insertBtn: any;
  deleteBtn: any;
  showSelectedOnlyBtn: any;
};

export class AddUsersToGroup extends React.Component<
  AddUsersToGroupProps,
  AddUsersToGroupState
> {
  constructor(props: AddUsersToGroupProps) {
    super(props);

    this.state = {
      selection: [],
    };
  }

  componentDidUpdate(prevProps: AddUsersToGroupProps) {
    if (prevProps.group.users != this.props.group.users) {
      this.setState({
        selection: this.props.group.users.map((user) => user.id),
      });
    }
  }

  createCustomButtonGroup(_: BootstrapTableButtonGroup) {
    const userIdSet = new Set(this.props.group.users.map((user) => user.id));
    const usersToAdd = this.state.selection.filter(
      (userId) => !userIdSet.has(userId)
    );
    return (
      <Button
        bsStyle="info"
        onClick={() => this.props.addUsersToGroup(usersToAdd)}
        disabled={usersToAdd.length == 0}
      >
        Add selected users to group
      </Button>
    );
  }

  onRowSelect(row: User, isSelected: Boolean, e: any) {
    let select_key = row.id;
    const original_selection: any = this.state.selection;

    let updated_selection: Array<string>;

    let index = original_selection.indexOf(select_key);
    if (index !== -1) {
      updated_selection = update(original_selection, {
        $splice: [[index, 1]],
      });
    } else {
      updated_selection = update(original_selection, {
        $push: [select_key],
      });
    }

    this.setState({ selection: updated_selection });
  }

  onAllRowsSelect(isSelected: Boolean, rows: Array<User>) {
    const original_selection: ReadonlyArray<string> = this.state.selection;
    let updated_selection: ReadonlyArray<string> = original_selection;

    let select_key = null;
    let index = null;
    rows.forEach((row) => {
      select_key = row.id;
      index = updated_selection.indexOf(select_key);

      if (index != -1) {
        updated_selection = update(updated_selection, {
          $splice: [[index, 1]],
        });
      } else {
        updated_selection = update(updated_selection, {
          $push: [select_key],
        });
      }
    });

    this.setState({ selection: updated_selection });
  }

  render() {
    const options = {
      btnGroup: this.createCustomButtonGroup.bind(this),
    };
    const selectRow = {
      mode: "checkbox",
      selected: this.state.selection,
      unselectable: this.props.group.users.map((user) => user.id),
      onSelect: (row: User, isSelected: Boolean, e: any) => {
        this.onRowSelect(row, isSelected, e);
        return true;
      },
      onSelectAll: (
        isSelected: Boolean,
        currentSelectedAndDisplayData: Array<User>
      ) => {
        this.onAllRowsSelect(isSelected, currentSelectedAndDisplayData);
        return true;
      },
    };
    const userIdSet = new Set(this.props.group.users.map((user) => user.id));
    const usersToAdd = this.state.selection.filter(
      (userId) => !userIdSet.has(userId)
    );
    return (
      <Modal
        style={modalStyles}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        onRequestClose={this.props.cancel}
        contentLabel="Share entries"
      >
        <div className="modal-content">
          <div className="modal-header">
            <h2 ref="subtitle">
              Add users to group <em>{this.props.group.name}</em>
            </h2>
          </div>
          <div className="modal-body">
            <BootstrapTable
              data={this.props.allUsers}
              options={options}
              selectRow={selectRow}
              search
              bordered={false}
              striped
              pagination
            >
              <TableHeaderColumn dataField="id" isKey hidden searchable={false}>
                ID
              </TableHeaderColumn>
              <TableHeaderColumn dataField="name" dataSort>
                User Name
              </TableHeaderColumn>
            </BootstrapTable>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-default"
              onClick={() => {
                if (
                  (usersToAdd.length > 0 &&
                    window.confirm(
                      "You have selected users to add to the group, but haven't saved the group ('Add selected users to group'). Close this modal anyway?"
                    )) ||
                  usersToAdd.length == 0
                ) {
                  this.props.cancel();
                  this.setState({
                    selection: this.props.group.users.map((user) => user.id),
                  });
                }
              }}
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    );
  }
}
