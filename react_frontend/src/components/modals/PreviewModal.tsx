import * as React from "react";
import * as Modal from "react-modal";
import { TaigaApi } from "../../models/api";
import { DatafilePreview } from "../../models/models";
import styles from "./PreviewModal.scss";

interface PreviewModalProps {
  isOpen: boolean;
  datafileId: string | null;
  datafileName: string | null;
  tapi: TaigaApi;
  onClose: () => void;
}

interface PreviewModalState {
  loading: boolean;
  preview: DatafilePreview | null;
  error: string | null;
}

export class PreviewModal extends React.Component<
  PreviewModalProps,
  PreviewModalState
> {
  private lastFetchedId: string | null = null;

  constructor(props: PreviewModalProps) {
    super(props);
    this.state = {
      loading: false,
      preview: null,
      error: null,
    };
  }

  componentDidUpdate(prevProps: PreviewModalProps) {
    if (
      this.props.isOpen &&
      this.props.datafileId &&
      this.props.datafileId !== this.lastFetchedId
    ) {
      this.fetchPreview(this.props.datafileId);
    }

    if (!this.props.isOpen && prevProps.isOpen) {
      this.lastFetchedId = null;
    }
  }

  fetchPreview(datafileId: string) {
    this.lastFetchedId = datafileId;
    this.setState({ loading: true, preview: null, error: null });

    this.props.tapi
      .get_datafile_preview(datafileId)
      .then((preview) => {
        this.setState({ loading: false, preview });
      })
      .catch((err) => {
        this.setState({
          loading: false,
          error: err.message || "Failed to load preview",
        });
      });
  }

  formatNumber(n: number): string {
    return n.toLocaleString();
  }

  renderDimensions(): string | null {
    const { preview } = this.state;
    if (!preview) return null;

    const parts: string[] = [];
    if (preview.num_rows != null) {
      parts.push(this.formatNumber(preview.num_rows) + " rows");
    }
    if (preview.num_columns != null) {
      parts.push(this.formatNumber(preview.num_columns) + " columns");
    }
    return parts.length > 0 ? parts.join(" \u00d7 ") : null;
  }

  renderFooter(): React.ReactNode {
    const { preview } = this.state;
    if (!preview || !preview.top_left_preview) return null;

    const tlp = preview.top_left_preview;
    const shownRows = tlp.data.length;
    const shownCols = tlp.column_names.length;
    const totalRows = preview.num_rows;
    const totalCols = preview.num_columns;

    if (totalRows == null && totalCols == null) return null;

    const parts: string[] = [];
    if (totalRows != null) {
      parts.push(
        shownRows + " of " + this.formatNumber(totalRows) + " rows"
      );
    }
    if (totalCols != null) {
      parts.push(
        shownCols + " of " + this.formatNumber(totalCols) + " columns"
      );
    }

    return (
      <div className={styles.footerNote}>Showing {parts.join(" and ")}</div>
    );
  }

  renderTable(): React.ReactNode {
    const { preview } = this.state;
    if (!preview || !preview.top_left_preview) {
      return (
        <div className={styles.emptyState}>
          No preview data available for this file.
        </div>
      );
    }

    const tlp = preview.top_left_preview;
    const hasRowNames = tlp.row_names != null && tlp.row_names.length > 0;

    return (
      <div className={styles.tableWrapper}>
        <table className={"table table-bordered " + styles.previewTable}>
          <thead>
            <tr>
              {hasRowNames && <th className={styles.cornerCell}></th>}
              {tlp.column_names.map((col, i) => (
                <th key={i}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tlp.data.map((row, rowIdx) => (
              <tr key={rowIdx}>
                {hasRowNames && (
                  <td className={styles.rowNameCell}>
                    {tlp.row_names![rowIdx]}
                  </td>
                )}
                {row.map((cell, colIdx) => (
                  <td key={colIdx}>
                    {cell == null ? (
                      <span style={{ color: "#ccc" }}>null</span>
                    ) : (
                      String(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  renderBody(): React.ReactNode {
    if (this.state.loading) {
      return (
        <div className={styles.loadingContainer}>Loading preview...</div>
      );
    }

    if (this.state.error) {
      return (
        <div className={styles.emptyState}>
          Error loading preview: {this.state.error}
        </div>
      );
    }

    if (!this.state.preview) {
      return (
        <div className={styles.emptyState}>
          No preview available for this file.
        </div>
      );
    }

    return (
      <div>
        {this.renderTable()}
        {this.renderFooter()}
      </div>
    );
  }

  render() {
    const dimensions = this.renderDimensions();

    return (
      <Modal
        className={styles.Modal}
        overlayClassName={styles.Overlay}
        ariaHideApp={false}
        closeTimeoutMS={150}
        isOpen={this.props.isOpen}
        onRequestClose={this.props.onClose}
        contentLabel="Data Preview"
      >
        <div className="modal-content">
          <div className="modal-header">
            <button
              type="button"
              className="close"
              onClick={this.props.onClose}
              aria-label="Close"
            >
              <span aria-hidden="true">&times;</span>
            </button>
            <h4 className="modal-title">
              {this.props.datafileName || "Preview"}
              {dimensions && (
                <span className={styles.dimensionsBadge}>{dimensions}</span>
              )}
            </h4>
          </div>
          <div className={styles.modalBody}>{this.renderBody()}</div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-default"
              onClick={this.props.onClose}
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    );
  }
}
