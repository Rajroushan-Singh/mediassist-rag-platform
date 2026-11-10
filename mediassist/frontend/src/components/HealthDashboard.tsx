import React, { useState } from "react";
import {
    Activity,
    AlertCircle,
    Calendar,
    CheckCircle2,
    Pill,
    Plus,
    Printer,
    Stethoscope,
    Trash2,
    User as UserIcon,
} from "lucide-react";
import type {
    HealthProfile,
    MedicalCondition,
    Medication,
    Treatment,
    User,
} from "../types";

interface HealthDashboardProps {
    user: User;
    profile: HealthProfile | null;
    conditions: MedicalCondition[];
    medications: Medication[];
    treatments: Treatment[];
    loading: boolean;
    message: string;
    error: string;
    onSaveProfile: (dob: string | null, sex: string | null, notes: string | null) => Promise<void>;
    onAddCondition: (name: string, status: string, date: string | null, notes: string | null) => Promise<void>;
    onDeleteCondition: (id: number) => Promise<void>;
    onAddMedication: (name: string, status: string, date: string | null, notes: string | null) => Promise<void>;
    onDeleteMedication: (id: number) => Promise<void>;
    onAddTreatment: (name: string, type: string | null, status: string, date: string | null, notes: string | null) => Promise<void>;
    onDeleteTreatment: (id: number) => Promise<void>;
    onBackToChat: () => void;
}

export const HealthDashboard: React.FC<HealthDashboardProps> = ({
    user: _user,
    profile,
    conditions,
    medications,
    treatments,
    loading,
    message,
    error,
    onSaveProfile,
    onAddCondition,
    onDeleteCondition,
    onAddMedication,
    onDeleteMedication,
    onAddTreatment,
    onDeleteTreatment,
    onBackToChat,
}) => {
    const [activeTab, setActiveTab] = useState<"profile" | "conditions" | "medications" | "treatments">("profile");

    // Profile form
    const [dob, setDob] = useState(profile?.date_of_birth || "");
    const [sex, setSex] = useState(profile?.biological_sex || "");
    const [notes, setNotes] = useState(profile?.health_notes || "");

    // Add forms state
    const [condName, setCondName] = useState("");
    const [condStatus, setCondStatus] = useState("active");
    const [condDate, setCondDate] = useState("");
    const [condNotes, setCondNotes] = useState("");

    const [medName, setMedName] = useState("");
    const [medStatus, setMedStatus] = useState("active");
    const [medDate, setMedDate] = useState("");
    const [medNotes, setMedNotes] = useState("");

    const [treatName, setTreatName] = useState("");
    const [treatType, setTreatType] = useState("");
    const [treatStatus, setTreatStatus] = useState("active");
    const [treatDate, setTreatDate] = useState("");
    const [treatNotes, setTreatNotes] = useState("");

    const handleProfileSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await onSaveProfile(dob || null, sex || null, notes || null);
    };

    const handleConditionSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!condName.trim()) return;
        await onAddCondition(condName.trim(), condStatus, condDate || null, condNotes.trim() || null);
        setCondName("");
        setCondDate("");
        setCondNotes("");
    };

    const handleMedicationSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!medName.trim()) return;
        await onAddMedication(medName.trim(), medStatus, medDate || null, medNotes.trim() || null);
        setMedName("");
        setMedDate("");
        setMedNotes("");
    };

    const handleTreatmentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!treatName.trim()) return;
        await onAddTreatment(treatName.trim(), treatType.trim() || null, treatStatus, treatDate || null, treatNotes.trim() || null);
        setTreatName("");
        setTreatType("");
        setTreatDate("");
        setTreatNotes("");
    };

    const printHealthSummary = () => {
        window.print();
    };

    const activeConditionsCount = conditions.filter((c) => c.status === "active").length;
    const activeMedicationsCount = medications.filter((m) => m.status === "active").length;

    return (
        <div className="health-dashboard-container">
            {/* Top Bar */}
            <header className="health-top-bar">
                <div>
                    <h2>Personal Health Profile</h2>
                    <p className="health-top-subtitle">
                        Maintain your longitudinal medical profile for safe, personalized context during consultations.
                    </p>
                </div>
                <div className="health-top-actions">
                    <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={printHealthSummary}
                        title="Print or export health summary"
                    >
                        <Printer size={16} />
                        <span>Print Summary</span>
                    </button>
                    <button
                        type="button"
                        className="btn btn-primary"
                        onClick={onBackToChat}
                    >
                        <span>Return to Chat</span>
                    </button>
                </div>
            </header>

            {/* Quick Metrics Bar */}
            <div className="health-stats-grid">
                <div className="stat-card">
                    <div className="stat-icon bg-emerald">
                        <Activity size={20} />
                    </div>
                    <div className="stat-info">
                        <span className="stat-value">{activeConditionsCount}</span>
                        <span className="stat-label">Active Conditions</span>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon bg-blue">
                        <Pill size={20} />
                    </div>
                    <div className="stat-info">
                        <span className="stat-value">{activeMedicationsCount}</span>
                        <span className="stat-label">Active Medications</span>
                    </div>
                </div>

                <div className="stat-card">
                    <div className="stat-icon bg-purple">
                        <Stethoscope size={20} />
                    </div>
                    <div className="stat-info">
                        <span className="stat-value">{treatments.length}</span>
                        <span className="stat-label">Total Procedures / Treatments</span>
                    </div>
                </div>
            </div>

            {/* Feedback Notifications */}
            {message && (
                <div className="alert-box alert-success mb-4">
                    <CheckCircle2 size={16} />
                    <span>{message}</span>
                </div>
            )}
            {error && (
                <div className="alert-box alert-error mb-4">
                    <AlertCircle size={16} />
                    <span>{error}</span>
                </div>
            )}

            {/* Nav Tabs */}
            <div className="health-tabs-nav">
                <button
                    type="button"
                    className={`health-nav-tab ${activeTab === "profile" ? "active" : ""}`}
                    onClick={() => setActiveTab("profile")}
                >
                    <UserIcon size={16} />
                    <span>Profile & Vitals</span>
                </button>
                <button
                    type="button"
                    className={`health-nav-tab ${activeTab === "conditions" ? "active" : ""}`}
                    onClick={() => setActiveTab("conditions")}
                >
                    <Activity size={16} />
                    <span>Conditions ({conditions.length})</span>
                </button>
                <button
                    type="button"
                    className={`health-nav-tab ${activeTab === "medications" ? "active" : ""}`}
                    onClick={() => setActiveTab("medications")}
                >
                    <Pill size={16} />
                    <span>Medications ({medications.length})</span>
                </button>
                <button
                    type="button"
                    className={`health-nav-tab ${activeTab === "treatments" ? "active" : ""}`}
                    onClick={() => setActiveTab("treatments")}
                >
                    <Stethoscope size={16} />
                    <span>Treatments ({treatments.length})</span>
                </button>
            </div>

            {/* Tab Contents */}
            <div className="health-tab-content">
                {/* 1. HEALTH PROFILE TAB */}
                {activeTab === "profile" && (
                    <div className="health-section-card">
                        <h3>General Health Demographics</h3>
                        <p className="card-desc">
                            Your biological details help MediAssist evaluate relevant age and sex-specific clinical reference ranges.
                        </p>

                        <form onSubmit={handleProfileSubmit} className="health-form">
                            <div className="form-row-2">
                                <div className="input-group">
                                    <label htmlFor="p-dob">Date of Birth</label>
                                    <input
                                        id="p-dob"
                                        type="date"
                                        value={dob}
                                        onChange={(e) => setDob(e.target.value)}
                                        disabled={loading}
                                    />
                                </div>

                                <div className="input-group">
                                    <label htmlFor="p-sex">Biological Sex</label>
                                    <select
                                        id="p-sex"
                                        value={sex}
                                        onChange={(e) => setSex(e.target.value)}
                                        disabled={loading}
                                    >
                                        <option value="">Prefer not to disclose</option>
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                            </div>

                            <div className="input-group">
                                <label htmlFor="p-notes">General Medical & Allergy Notes</label>
                                <textarea
                                    id="p-notes"
                                    rows={4}
                                    placeholder="List any known drug allergies, dietary restrictions, baseline health context, or family history..."
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    maxLength={5000}
                                    disabled={loading}
                                />
                            </div>

                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={loading}
                            >
                                {loading ? "Saving..." : "Save Health Profile"}
                            </button>
                        </form>
                    </div>
                )}

                {/* 2. CONDITIONS TAB */}
                {activeTab === "conditions" && (
                    <div className="health-section-card">
                        <div className="card-header-between">
                            <div>
                                <h3>Medical Conditions & Diagnoses</h3>
                                <p className="card-desc">Keep track of chronic or resolved health conditions.</p>
                            </div>
                        </div>

                        {/* Add Condition Form */}
                        <form onSubmit={handleConditionSubmit} className="add-record-form">
                            <div className="form-row-3">
                                <input
                                    type="text"
                                    placeholder="Condition name (e.g. Hypertension, Asthma)"
                                    value={condName}
                                    onChange={(e) => setCondName(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                                <select
                                    value={condStatus}
                                    onChange={(e) => setCondStatus(e.target.value)}
                                    disabled={loading}
                                >
                                    <option value="active">Active</option>
                                    <option value="past">Past</option>
                                    <option value="resolved">Resolved</option>
                                </select>
                                <input
                                    type="date"
                                    value={condDate}
                                    onChange={(e) => setCondDate(e.target.value)}
                                    disabled={loading}
                                />
                            </div>
                            <div className="form-row-notes">
                                <input
                                    type="text"
                                    placeholder="Notes (optional, e.g. diagnosed by Dr. Evans, well controlled)"
                                    value={condNotes}
                                    onChange={(e) => setCondNotes(e.target.value)}
                                    disabled={loading}
                                />
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={loading || !condName.trim()}
                                >
                                    <Plus size={16} />
                                    <span>Add Condition</span>
                                </button>
                            </div>
                        </form>

                        {/* Condition List */}
                        <div className="records-grid">
                            {conditions.length === 0 ? (
                                <p className="empty-records">No medical conditions recorded yet.</p>
                            ) : (
                                conditions.map((c) => (
                                    <div key={c.id} className="record-card">
                                        <div className="record-main">
                                            <div className="record-title-row">
                                                <h4>{c.condition_name}</h4>
                                                <span className={`status-badge status-${c.status}`}>
                                                    {c.status}
                                                </span>
                                            </div>
                                            {c.diagnosed_date && (
                                                <div className="record-meta">
                                                    <Calendar size={13} />
                                                    <span>Diagnosed: {c.diagnosed_date}</span>
                                                </div>
                                            )}
                                            {c.notes && <p className="record-notes">{c.notes}</p>}
                                        </div>
                                        <button
                                            type="button"
                                            className="record-delete-btn"
                                            onClick={() => onDeleteCondition(c.id)}
                                            title="Remove condition"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                {/* 3. MEDICATIONS TAB */}
                {activeTab === "medications" && (
                    <div className="health-section-card">
                        <div className="card-header-between">
                            <div>
                                <h3>Medications & Prescriptions</h3>
                                <p className="card-desc">Track active pharmaceuticals, vitamins, and supplements.</p>
                            </div>
                        </div>

                        {/* Add Medication Form */}
                        <form onSubmit={handleMedicationSubmit} className="add-record-form">
                            <div className="form-row-3">
                                <input
                                    type="text"
                                    placeholder="Medication name (e.g. Metformin 500mg, Lisinopril 10mg)"
                                    value={medName}
                                    onChange={(e) => setMedName(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                                <select
                                    value={medStatus}
                                    onChange={(e) => setMedStatus(e.target.value)}
                                    disabled={loading}
                                >
                                    <option value="active">Active</option>
                                    <option value="past">Past</option>
                                    <option value="discontinued">Discontinued</option>
                                </select>
                                <input
                                    type="date"
                                    value={medDate}
                                    onChange={(e) => setMedDate(e.target.value)}
                                    disabled={loading}
                                />
                            </div>
                            <div className="form-row-notes">
                                <input
                                    type="text"
                                    placeholder="Dosage instructions (e.g. 1 tablet twice daily with meals)"
                                    value={medNotes}
                                    onChange={(e) => setMedNotes(e.target.value)}
                                    disabled={loading}
                                />
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={loading || !medName.trim()}
                                >
                                    <Plus size={16} />
                                    <span>Add Medication</span>
                                </button>
                            </div>
                        </form>

                        {/* Medication List */}
                        <div className="records-grid">
                            {medications.length === 0 ? (
                                <p className="empty-records">No medications recorded yet.</p>
                            ) : (
                                medications.map((m) => (
                                    <div key={m.id} className="record-card">
                                        <div className="record-main">
                                            <div className="record-title-row">
                                                <h4>{m.medication_name}</h4>
                                                <span className={`status-badge status-${m.status}`}>
                                                    {m.status}
                                                </span>
                                            </div>
                                            {m.start_date && (
                                                <div className="record-meta">
                                                    <Calendar size={13} />
                                                    <span>Started: {m.start_date}</span>
                                                </div>
                                            )}
                                            {m.notes && <p className="record-notes">{m.notes}</p>}
                                        </div>
                                        <button
                                            type="button"
                                            className="record-delete-btn"
                                            onClick={() => onDeleteMedication(m.id)}
                                            title="Remove medication"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                {/* 4. TREATMENTS TAB */}
                {activeTab === "treatments" && (
                    <div className="health-section-card">
                        <div className="card-header-between">
                            <div>
                                <h3>Treatments, Therapies & Surgeries</h3>
                                <p className="card-desc">Log past or ongoing medical treatments and physical therapies.</p>
                            </div>
                        </div>

                        {/* Add Treatment Form */}
                        <form onSubmit={handleTreatmentSubmit} className="add-record-form">
                            <div className="form-row-3">
                                <input
                                    type="text"
                                    placeholder="Treatment name (e.g. Physical Therapy, Knee Arthroscopy)"
                                    value={treatName}
                                    onChange={(e) => setTreatName(e.target.value)}
                                    required
                                    disabled={loading}
                                />
                                <input
                                    type="text"
                                    placeholder="Type (e.g. Surgical, Therapy, Lifestyle)"
                                    value={treatType}
                                    onChange={(e) => setTreatType(e.target.value)}
                                    disabled={loading}
                                />
                                <select
                                    value={treatStatus}
                                    onChange={(e) => setTreatStatus(e.target.value)}
                                    disabled={loading}
                                >
                                    <option value="active">Active</option>
                                    <option value="past">Past</option>
                                    <option value="completed">Completed</option>
                                </select>
                            </div>
                            <div className="form-row-notes">
                                <input
                                    type="date"
                                    value={treatDate}
                                    onChange={(e) => setTreatDate(e.target.value)}
                                    disabled={loading}
                                />
                                <input
                                    type="text"
                                    placeholder="Outcome / notes (optional)"
                                    value={treatNotes}
                                    onChange={(e) => setTreatNotes(e.target.value)}
                                    disabled={loading}
                                />
                                <button
                                    type="submit"
                                    className="btn btn-primary"
                                    disabled={loading || !treatName.trim()}
                                >
                                    <Plus size={16} />
                                    <span>Add Treatment</span>
                                </button>
                            </div>
                        </form>

                        {/* Treatments List */}
                        <div className="records-grid">
                            {treatments.length === 0 ? (
                                <p className="empty-records">No treatments or surgeries recorded yet.</p>
                            ) : (
                                treatments.map((t) => (
                                    <div key={t.id} className="record-card">
                                        <div className="record-main">
                                            <div className="record-title-row">
                                                <h4>{t.treatment_name}</h4>
                                                <span className={`status-badge status-${t.status}`}>
                                                    {t.status}
                                                </span>
                                            </div>
                                            {t.treatment_type && (
                                                <div className="record-meta">
                                                    <Stethoscope size={13} />
                                                    <span>Category: {t.treatment_type}</span>
                                                </div>
                                            )}
                                            {t.start_date && (
                                                <div className="record-meta">
                                                    <Calendar size={13} />
                                                    <span>Date: {t.start_date}</span>
                                                </div>
                                            )}
                                            {t.notes && <p className="record-notes">{t.notes}</p>}
                                        </div>
                                        <button
                                            type="button"
                                            className="record-delete-btn"
                                            onClick={() => onDeleteTreatment(t.id)}
                                            title="Remove treatment"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
