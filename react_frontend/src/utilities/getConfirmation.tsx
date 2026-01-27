import * as React from "react";
import * as ReactDOM from "react-dom";
import { Button, Modal } from "react-bootstrap";
import styles from "../styles/utilities.scss";

interface ConfirmationOptions {
  title?: string | null;
  yesText?: string | null;
  noText?: string | null;
  message: React.ReactNode;
  showModalBackdrop?: boolean | null;
  yesButtonBsStyle?: string | null | undefined;
  dontShowAgainLocalStorageKey?: string;
}

const launchModal = (
  options: ConfirmationOptions,
  resolve: (ok: boolean) => void
) => {
  if (options.dontShowAgainLocalStorageKey) {
    const skip =
      window.localStorage.getItem(options.dontShowAgainLocalStorageKey!) ===
      "true";

    if (skip) {
      resolve(true);
      return;
    }
  }

  const container = document.createElement("div");
  container.id = "confirmation-modal-container";
  document.body.append(container);

  const unmount = () => {
    ReactDOM.unmountComponentAtNode(container);
    container.remove();
  };

  ReactDOM.render(
    <Modal
      show
      backdrop={
        typeof options.showModalBackdrop === "boolean"
          ? options.showModalBackdrop
          : true
      }
      onHide={() => {
        resolve(false);
        unmount();
      }}
    >
      <Modal.Header className={styles.confirmationHeader}>
        <Modal.Title>{options.title || "Are you sure?"}</Modal.Title>
      </Modal.Header>
      <Modal.Body className={styles.confirmationBody}>
        <section>{options.message}</section>
        {options.dontShowAgainLocalStorageKey && (
          <section className={styles.dontShowThisAgain}>
            <label>
              <input
                type="checkbox"
                defaultChecked={false}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                  if (e.target.checked) {
                    window.localStorage.setItem(
                      options.dontShowAgainLocalStorageKey!,
                      "true"
                    );
                  } else {
                    window.localStorage.removeItem(
                      options.dontShowAgainLocalStorageKey!
                    );
                  }
                }}
              />
              <span>Don’t show this again</span>
            </label>
          </section>
        )}
      </Modal.Body>
      <Modal.Footer>
        <Button
          onClick={() => {
            resolve(false);
            unmount();
          }}
        >
          {options.noText || "No"}
        </Button>
        <Button
          bsStyle={options.yesButtonBsStyle || "danger"}
          onClick={() => {
            resolve(true);
            unmount();
          }}
        >
          {options.yesText || "Yes"}
        </Button>
      </Modal.Footer>
    </Modal>,

    container
  );
};

export default function getConfirmation(options: ConfirmationOptions) {
  return new Promise<boolean>((resolve) => {
    launchModal(options, resolve);
  });
}
