import React from "react";
import { ShieldCheck, Lock, AlertCircle, CheckCircle2 } from "lucide-react";
import type { ConsentState } from "../types";

interface ConsentModalProps {
    consentState: ConsentState;
    consentError: string;
    consentSubmitting: boolean;
    onAccept: () => void;
    onWithdraw?: () => void;
    onRetry: () => void;
    onLogout: () => void;
}

export const ConsentModal: React.FC<ConsentModalProps> = ({
    consentState,
    consentError,
    consentSubmitting,
    onAccept,
    onRetry,
    onLogout,
}) => {
    return (
        <div className="auth-overlay">
            <div className="consent-modal-card">
                <div className="consent-badge">
                    <ShieldCheck size={28} className="text-emerald-500" />
                </div>
                <h2>Health Information & Privacy Consent</h2>
                <p className="consent-subhead">
                    MediAssist complies with strict health privacy standards. Before proceeding, please review how your health context is used.
                </p>

                <div className="consent-points">
                    <div className="consent-point">
                        <CheckCircle2 size={18} className="point-icon" />
                        <div>
                            <strong>Evidence-Based Clinical Guidance</strong>
                            <p>Information you share (symptoms, prescriptions, uploaded documents) is processed to retrieve verified medical literature.</p>
                        </div>
                    </div>
                    <div className="consent-point">
                        <Lock size={18} className="point-icon" />
                        <div>
                            <strong>Transient In-Memory Document Analysis</strong>
                            <p>Prescriptions and lab images are processed in memory with AI Vision and are not permanently archived or sold to third parties.</p>
                        </div>
                    </div>
                    <div className="consent-point">
                        <AlertCircle size={18} className="point-icon text-amber-500" />
                        <div>
                            <strong>Not a Substitute for Licensed Physicians</strong>
                            <p>MediAssist provides informational triage. Always consult with a qualified doctor for medical diagnoses or urgent care.</p>
                        </div>
                    </div>
                </div>

                {consentError && (
                    <div className="alert-box alert-error">
                        <AlertCircle size={16} />
                        <span>{consentError}</span>
                    </div>
                )}

                <div className="consent-actions">
                    {consentState === "error" ? (
                        <button
                            type="button"
                            className="btn btn-primary btn-block"
                            onClick={onRetry}
                        >
                            Retry Connection
                        </button>
                    ) : (
                        <button
                            type="button"
                            className="btn btn-primary btn-block"
                            onClick={onAccept}
                            disabled={consentSubmitting}
                        >
                            {consentSubmitting ? "Saving Preference..." : "I Agree & Continue"}
                        </button>
                    )}
                    <button
                        type="button"
                        className="btn btn-ghost btn-block"
                        onClick={onLogout}
                    >
                        Decline & Log Out
                    </button>
                </div>
            </div>
        </div>
    );
};
