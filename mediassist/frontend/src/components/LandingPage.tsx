import React, { useState } from "react";
import {
    AlertTriangle,
    Camera,
    CheckCircle2,
    ChevronRight,
    FileSearch,
    FileText,
    HeartPulse,
    Lock,
    Mic,
    ShieldCheck,
    Sparkles,
    Stethoscope,
} from "lucide-react";

interface LandingPageProps {
    onOpenAuth: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onOpenAuth }) => {
    const [activeDemoTab, setActiveDemoTab] = useState<"vision" | "rag" | "triage">("vision");

    return (
        <div className="landing-container">
            {/* Top Navigation */}
            <header className="landing-nav">
                <div className="landing-nav-inner">
                    <div className="landing-brand">
                        <div className="brand-icon-box">
                            <HeartPulse size={24} className="text-emerald-500" />
                        </div>
                        <span className="brand-name">MediAssist</span>
                        <span className="version-pill">v2.0 Vision</span>
                    </div>

                    <nav className="landing-nav-links">
                        <a href="#features">Features</a>
                        <a href="#vision">Multimodal Vision</a>
                        <a href="#demo">Interactive Demo</a>
                        <a href="#security">Privacy & Safety</a>
                        <a href="#faq">FAQ</a>
                    </nav>

                    <div className="landing-nav-actions">
                        <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={onOpenAuth}
                        >
                            Sign In
                        </button>
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={onOpenAuth}
                        >
                            Get Started Free
                        </button>
                    </div>
                </div>
            </header>

            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-badge">
                    <Sparkles size={14} className="text-emerald-400" />
                    <span>Powered by Gemini Multimodal Vision & FAISS Medical RAG</span>
                </div>

                <h1 className="hero-title">
                    Clinical Intelligence, <br />
                    <span className="gradient-text">Visual Clarity</span> for Every Patient
                </h1>

                <p className="hero-subtitle">
                    Upload doctor prescriptions, lab test reports, or describe your symptoms.
                    MediAssist combines state-of-the-art vision models and verified medical literature
                    to deliver clear, evidence-based health guidance in seconds.
                </p>

                <div className="hero-cta-group">
                    <button
                        type="button"
                        className="btn btn-primary btn-xl"
                        onClick={onOpenAuth}
                    >
                        <span>Start Free Health Consultation</span>
                        <ChevronRight size={20} />
                    </button>
                    <a href="#demo" className="btn btn-secondary btn-xl">
                        <span>Explore Capabilities</span>
                    </a>
                </div>

                {/* Trust Badges */}
                <div className="hero-trust-bar">
                    <div className="trust-item">
                        <Camera size={18} className="text-emerald-500" />
                        <span>Prescription & Lab OCR</span>
                    </div>
                    <div className="trust-divider"></div>
                    <div className="trust-item">
                        <ShieldCheck size={18} className="text-emerald-500" />
                        <span>Zero Data Selling</span>
                    </div>
                    <div className="trust-divider"></div>
                    <div className="trust-item">
                        <AlertTriangle size={18} className="text-amber-500" />
                        <span>Deterministic Emergency Triaging</span>
                    </div>
                    <div className="trust-divider"></div>
                    <div className="trust-item">
                        <Mic size={18} className="text-emerald-500" />
                        <span>Voice-Enabled Consultation</span>
                    </div>
                </div>
            </section>

            {/* Interactive Demo Showcase */}
            <section id="demo" className="demo-section">
                <div className="section-header">
                    <span className="section-tag">Interactive Preview</span>
                    <h2>See MediAssist in Action</h2>
                    <p>Select a medical workflow below to preview how our multimodal assistant responds.</p>
                </div>

                <div className="demo-card">
                    <div className="demo-tabs">
                        <button
                            type="button"
                            className={`demo-tab ${activeDemoTab === "vision" ? "active" : ""}`}
                            onClick={() => setActiveDemoTab("vision")}
                        >
                            <Camera size={16} />
                            <span>Prescription & Lab Vision</span>
                        </button>
                        <button
                            type="button"
                            className={`demo-tab ${activeDemoTab === "rag" ? "active" : ""}`}
                            onClick={() => setActiveDemoTab("rag")}
                        >
                            <FileSearch size={16} />
                            <span>Evidence-Based Medical QA</span>
                        </button>
                        <button
                            type="button"
                            className={`demo-tab ${activeDemoTab === "triage" ? "active" : ""}`}
                            onClick={() => setActiveDemoTab("triage")}
                        >
                            <AlertTriangle size={16} />
                            <span>Emergency Life Safety</span>
                        </button>
                    </div>

                    <div className="demo-window">
                        {activeDemoTab === "vision" && (
                            <div className="demo-content">
                                <div className="demo-user-msg">
                                    <div className="demo-attachment-chip">
                                        <FileText size={16} />
                                        <span>prescription_amoxicillin_500mg.png</span>
                                        <span className="badge-vision-ready">Vision Processed</span>
                                    </div>
                                    <p>I got this prescription from my doctor today. What are the key directions, side effects, and precautions?</p>
                                </div>
                                <div className="demo-bot-msg">
                                    <div className="demo-bot-header">
                                        <div className="bot-avatar"><Stethoscope size={16} /></div>
                                        <strong>MediAssist Clinical Intelligence</strong>
                                    </div>
                                    <div className="demo-markdown">
                                        <h4>📋 Extracted Prescription Analysis</h4>
                                        <ul>
                                            <li><strong>Medication:</strong> Amoxicillin 500mg (Penicillin antibiotic)</li>
                                            <li><strong>Sig / Instructions:</strong> 1 capsule three times daily (every 8 hours) with or without food.</li>
                                            <li><strong>Course Duration:</strong> 7 full days (complete entire course even if feeling recovered).</li>
                                        </ul>
                                        <h4>⚠️ Key Safety Precautions</h4>
                                        <p>Do not use if you have a documented allergy to penicillins or cephalosporins. Report any rash, severe diarrhea, or facial swelling immediately.</p>
                                    </div>
                                    <div className="demo-sources-pill">
                                        <span>Verified with Curated Antibiotic Therapy Guidelines (Page 142)</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeDemoTab === "rag" && (
                            <div className="demo-content">
                                <div className="demo-user-msg">
                                    <p>My fasting glucose came back at 118 mg/dL. Is this considered prediabetes, and what lifestyle modifications should I ask my doctor about?</p>
                                </div>
                                <div className="demo-bot-msg">
                                    <div className="demo-bot-header">
                                        <div className="bot-avatar"><Stethoscope size={16} /></div>
                                        <strong>MediAssist Clinical Intelligence</strong>
                                    </div>
                                    <div className="demo-markdown">
                                        <p>According to American Diabetes Association clinical guidelines:</p>
                                        <ul>
                                            <li><strong>Normal Fasting Glucose:</strong> &lt; 100 mg/dL</li>
                                            <li><strong>Impaired Fasting Glucose (Prediabetes):</strong> 100 – 125 mg/dL</li>
                                            <li><strong>Diabetes Threshold:</strong> &ge; 126 mg/dL (confirmed on repeat testing)</li>
                                        </ul>
                                        <p>A fasting level of 118 mg/dL falls into the <strong>impaired fasting glucose (prediabetes)</strong> range. Recommended conversation points with your physician include an HbA1c test, physical activity goals (150 min/week), and dietary fiber optimization.</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeDemoTab === "triage" && (
                            <div className="demo-content">
                                <div className="demo-user-msg">
                                    <p>I have sudden crushing chest pressure spreading to my left shoulder and jaw, and feeling dizzy.</p>
                                </div>
                                <div className="demo-bot-msg emergency-demo">
                                    <div className="emergency-alert-banner">
                                        <AlertTriangle size={24} className="text-red-500" />
                                        <div>
                                            <strong>CRITICAL EMERGENCY NOTICE</strong>
                                            <p>Your described symptoms indicate a potential cardiac emergency (such as a heart attack). Do NOT wait or drive yourself.</p>
                                        </div>
                                    </div>
                                    <p className="emergency-instructions">
                                        <strong>Call 911 or your local emergency number immediately.</strong> Sit or lie down in a safe position, loosen tight clothing, and unlock your front door for emergency responders.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* Feature Highlights Grid */}
            <section id="features" className="features-grid-section">
                <div className="section-header">
                    <span className="section-tag">Platform Capabilities</span>
                    <h2>Engineered for Modern Healthcare Consumer Needs</h2>
                    <p>Designed with medical safety boundaries, privacy compliance, and intuitive speed.</p>
                </div>

                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon-box bg-emerald">
                            <Camera size={24} />
                        </div>
                        <h3>Multimodal Image & Document OCR</h3>
                        <p>Upload photos of doctor prescriptions, blood tests, metabolic panels, or skin symptoms. MediAssist instantly transcribes values, flags out-of-range results, and structures data.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-box bg-blue">
                            <FileSearch size={24} />
                        </div>
                        <h3>FAISS Vector Medical Retrieval</h3>
                        <p>Responses are grounded in verified clinical knowledge passages, preventing LLM hallucinations and citing specific medical sources.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-box bg-red">
                            <AlertTriangle size={24} />
                        </div>
                        <h3>Deterministic Life-Safety Triage</h3>
                        <p>Zero delay for acute medical risks. Immediate emergency triage flags chest pain, stroke symptoms, and anaphylaxis prior to any retrieval step.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-box bg-purple">
                            <HeartPulse size={24} />
                        </div>
                        <h3>Longitudinal Health Profile</h3>
                        <p>Maintain your active conditions, medication history, and personal health notes. The assistant references relevant personal context while respecting strict privacy.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-box bg-teal">
                            <Mic size={24} />
                        </div>
                        <h3>Voice Input & Audio Read-Aloud</h3>
                        <p>Speak your questions naturally using speech-to-text, and listen to detailed medical explanations hands-free with built-in voice playback.</p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon-box bg-amber">
                            <Lock size={24} />
                        </div>
                        <h3>HIPAA-Aligned Privacy & Consent</h3>
                        <p>Full control over your data. All document processing is transient in-memory. Easily withdraw health data consent at any time with a single click.</p>
                    </div>
                </div>
            </section>

            {/* Privacy & Security Section */}
            <section id="security" className="security-section">
                <div className="security-card">
                    <div className="security-content">
                        <div className="security-badge">
                            <ShieldCheck size={18} />
                            <span>Privacy & Security Architecture</span>
                        </div>
                        <h2>Your Health Data Belongs to You</h2>
                        <p>
                            Healthcare information is sensitive. MediAssist is built with strict architectural
                            guarantees: uploads are processed transiently in memory, no medical records are sold,
                            and you retain the right to withdraw health data consent anytime.
                        </p>
                        <div className="security-checklist">
                            <div className="check-item">
                                <CheckCircle2 size={18} className="text-emerald-400" />
                                <span>No permanent storage of uploaded medical documents or image files</span>
                            </div>
                            <div className="check-item">
                                <CheckCircle2 size={18} className="text-emerald-400" />
                                <span>Deterministic safety boundaries preventing unsupervised diagnosis</span>
                            </div>
                            <div className="check-item">
                                <CheckCircle2 size={18} className="text-emerald-400" />
                                <span>Granular consent tracking with instant opt-out locking</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* FAQ Section */}
            <section id="faq" className="faq-section">
                <div className="section-header">
                    <span className="section-tag">Frequently Asked Questions</span>
                    <h2>Everything You Need to Know</h2>
                </div>

                <div className="faq-list">
                    <div className="faq-item">
                        <h4>Can I upload a picture of my doctor's handwritten prescription?</h4>
                        <p>Yes. MediAssist uses Gemini Multimodal Vision to accurately transcribe handwritten drug names, dosages, and sig instructions, providing you with a structured breakdown and key safety precautions.</p>
                    </div>
                    <div className="faq-item">
                        <h4>Does MediAssist replace visiting a doctor?</h4>
                        <p>No. MediAssist provides evidence-based health information to help you understand medical terms, reports, and questions to ask your doctor. It does not provide medical diagnoses or replace care from licensed medical professionals.</p>
                    </div>
                    <div className="faq-item">
                        <h4>What happens if I enter an emergency symptom?</h4>
                        <p>MediAssist runs a deterministic emergency classifier before generating any AI response. If acute life-threatening symptoms are detected, an immediate alert directs you to call 911/112 or visit the nearest emergency room.</p>
                    </div>
                </div>
            </section>

            {/* Final CTA Banner */}
            <section className="final-cta-section">
                <div className="final-cta-box">
                    <h2>Ready to Experience Next-Gen Health AI?</h2>
                    <p>Start a consultation now or upload a prescription to see instant multimodal clinical extraction.</p>
                    <button
                        type="button"
                        className="btn btn-primary btn-xl"
                        onClick={onOpenAuth}
                    >
                        <span>Get Started with MediAssist</span>
                        <ChevronRight size={20} />
                    </button>
                </div>
            </section>

            {/* Footer */}
            <footer className="landing-footer">
                <div className="footer-inner">
                    <div className="footer-brand">
                        <div className="landing-brand">
                            <HeartPulse size={20} className="text-emerald-500" />
                            <span className="brand-name">MediAssist</span>
                        </div>
                        <p className="footer-tagline">
                            Evidence-grounded medical AI companion for prescriptions, lab tests, and clinical inquiries.
                        </p>
                    </div>

                    <div className="footer-disclaimer-box">
                        <strong>Medical Disclaimer:</strong> MediAssist is an artificial intelligence platform for general health educational purposes only. It is not a licensed healthcare provider, does not establish a doctor-patient relationship, and does not provide clinical diagnoses or individualized prescription changes. Always consult a qualified physician for medical concerns. In an emergency, dial 911 or your local emergency number immediately.
                    </div>

                    <div className="footer-bottom">
                        <p>&copy; {new Date().getFullYear()} MediAssist Health Technologies. All rights reserved.</p>
                    </div>
                </div>
            </footer>
        </div>
    );
};
