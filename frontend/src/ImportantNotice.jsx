import React, { useEffect, useRef, useState } from "react";
import { X, ShieldAlert } from "lucide-react";
import {
  dismissImportantNotice,
  shouldShowImportantNotice,
} from "./importantNoticeSchedule";
import "./important-notice.css";

function getNoticeStorage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export default function ImportantNotice() {
  const [isOpen, setIsOpen] = useState(() => shouldShowImportantNotice(getNoticeStorage()));
  const closeButtonRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return undefined;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const closeOnEscape = (event) => {
      if (event.key === "Escape") closeNotice();
    };
    document.addEventListener("keydown", closeOnEscape);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [isOpen]);

  const closeNotice = () => {
    dismissImportantNotice(getNoticeStorage());
    setIsOpen(false);
  };

  if (!isOpen) return null;

  return (
    <div className="finos-notice-backdrop">
      <section
        className="finos-notice-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="finos-notice-title"
        aria-describedby="finos-notice-description"
      >
        <header className="finos-notice-header">
          <div className="finos-notice-heading">
            <span className="finos-notice-icon" aria-hidden="true"><ShieldAlert size={20} /></span>
            <div>
              <p className="finos-notice-eyebrow">FINANCIAL OS</p>
              <h2 id="finos-notice-title">Important Notice</h2>
            </div>
          </div>
          <button
            ref={closeButtonRef}
            type="button"
            className="finos-notice-close"
            onClick={closeNotice}
            aria-label="Close important notice"
            title="Close"
          >
            <X size={19} />
          </button>
        </header>

        <div className="finos-notice-content" id="finos-notice-description">
          <ol>
            <li>
              <strong>Individual use</strong>
              <p>This website and service are intended solely for individual, personal use.</p>
            </li>
            <li>
              <strong>Plans and pricing</strong>
              <p>Plans and pricing are displayed to give the website a complete, premium presentation. They do not represent a current offer of commercial services.</p>
            </li>
            <li>
              <strong>No commercial use at present</strong>
              <p>Commercial use of this application, website or service is not currently permitted or intended. Any decision to commercialise it would be considered no earlier than 3–5 years from now.</p>
            </li>
            <li>
              <strong>Licensing enquiries</strong>
              <p>For any licensing-related questions or concerns, please use the Contact Details section or submit the contact form.</p>
            </li>
          </ol>
        </div>

        <footer className="finos-notice-footer">
          <span>This notice will appear again tomorrow.</span>
          <button type="button" className="finos-notice-acknowledge" onClick={closeNotice}>
            Close notice
          </button>
        </footer>
      </section>
    </div>
  );
}
