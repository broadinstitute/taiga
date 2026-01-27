import * as React from "react";
import * as ReactDOM from "react-dom";
import { Button, Modal } from "react-bootstrap";

type ModalProps = React.ComponentProps<typeof Modal>;
type ModalPropsWithOptionalOnHide = Omit<ModalProps, "onHide"> & {
  onHide?: ModalProps["onHide"];
};

interface InfoModalOptions {
  title: string;
  content: React.ReactNode;
  closeButtonText?: string;
  modalProps?: ModalPropsWithOptionalOnHide;
}

function showInfoModal(
  options: InfoModalOptions
): Promise<void> {
  const container = document.createElement("div");
  container.id = "confirmation-modal-container";
  document.body.append(container);

  let resolveFn: () => void;

  const promise = new Promise<void>((resolve) => {
    resolveFn = resolve;
  });

  const unmount = () => {
    ReactDOM.unmountComponentAtNode(container);
    container.remove();
    resolveFn();
  };

  ReactDOM.render(
    <Modal
      backdrop="static"
      {...options.modalProps}
      show
      onHide={() => {
        options.modalProps?.onHide?.();
        unmount();
      }}
    >
      <Modal.Header>
        <Modal.Title>{options.title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <section>{options.content}</section>
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={unmount}>{options.closeButtonText || "Close"}</Button>
      </Modal.Footer>
    </Modal>,

    container
  );

  return promise;
}

export default  showInfoModal;
