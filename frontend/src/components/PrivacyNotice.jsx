import React from "react";
import { AlertTriangle } from "lucide-react";

export default function PrivacyNotice() {
  return (
    <div className="privacy-banner">
      <AlertTriangle size={20} style={{ flexShrink: 0 }} />
      <div>
        <strong>Consent-Based Face Recognition Privacy Notice:</strong> Face recognition in this project is intended only for authorized, consent-based demonstrations. Do not use biometric identification without appropriate authorization, consent, and applicable legal safeguards.
      </div>
    </div>
  );
}
