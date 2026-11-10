import { useEffect, useRef, useState } from "react";
import api from "./services/api";
import type {
    ConsentState,
    Conversation,
    ExtractedDocument,
    HealthProfile,
    MedicalCondition,
    Medication,
    Message,
    Treatment,
    User,
} from "./types";
import { LandingPage } from "./components/LandingPage";
import { AuthModal } from "./components/AuthModal";
import { ConsentModal } from "./components/ConsentModal";
import { Sidebar } from "./components/Sidebar";
import { ChatArea } from "./components/ChatArea";
import { HealthDashboard } from "./components/HealthDashboard";

export function App() {
    // Auth & User State
    const [user, setUser] = useState<User | null>(null);
    const [authLoading, setAuthLoading] = useState(false);
    const [authError, setAuthError] = useState("");
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

    // Consent State
    const [consentState, setConsentState] = useState<ConsentState>("checking");
    const [consentError, setConsentError] = useState("");
    const [consentSubmitting, setConsentSubmitting] = useState(false);

    // Navigation View
    const [activeView, setActiveView] = useState<"chat" | "health">("chat");
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

    // Conversation & Chat State
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeId, setActiveId] = useState<number | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [chatLoading, setChatLoading] = useState(false);
    const [conversationLoading, setConversationLoading] = useState(false);
    const [chatError, setChatError] = useState("");

    // Document & Image Extraction State
    const [documentLoading, setDocumentLoading] = useState(false);
    const [documentError, setDocumentError] = useState("");

    // Abort Controllers for Stop Agent & Document Cancellation
    const chatAbortControllerRef = useRef<AbortController | null>(null);
    const docAbortControllerRef = useRef<AbortController | null>(null);

    // Health Records State
    const [healthProfile, setHealthProfile] = useState<HealthProfile | null>(null);
    const [conditions, setConditions] = useState<MedicalCondition[]>([]);
    const [medications, setMedications] = useState<Medication[]>([]);
    const [treatments, setTreatments] = useState<Treatment[]>([]);
    const [healthLoading, setHealthLoading] = useState(false);
    const [healthMessage, setHealthMessage] = useState("");
    const [healthError, setHealthError] = useState("");

    // Initial Load
    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (token) {
            void loadUser();
        } else {
            setConsentState("required");
        }
    }, []);

    // Load User
    async function loadUser() {
        try {
            const response = await api.get("/auth/me");
            setUser(response.data);
            await loadConsent();
        } catch {
            localStorage.removeItem("access_token");
            setUser(null);
            setConsentState("required");
        }
    }

    // Consent Management
    async function loadConsent() {
        setConsentState("checking");
        setConsentError("");
        try {
            const response = await api.get("/consent");
            const records = Array.isArray(response.data)
                ? response.data
                : response.data?.consents || response.data?.items || [];
            const latest = records.find(
                (item: { consent_type?: string }) => item.consent_type === "health_information"
            );
            if (latest?.accepted === true && latest?.consent_version === "1.0") {
                setConsentState("accepted");
                await loadConversations();
            } else {
                setConsentState("required");
            }
        } catch (err: any) {
            setConsentState("error");
            setConsentError(
                err.response?.data?.detail || "Could not verify health data consent status."
            );
        }
    }

    async function acceptHealthConsent() {
        setConsentSubmitting(true);
        setConsentError("");
        try {
            await api.post("/consent", {
                consent_type: "health_information",
                consent_version: "1.0",
                accepted: true,
            });
            setConsentState("accepted");
            await loadConversations();
        } catch (err: any) {
            setConsentError(err.response?.data?.detail || "Could not record health information consent.");
        } finally {
            setConsentSubmitting(false);
        }
    }

    async function withdrawHealthConsent() {
        if (
            !window.confirm(
                "Withdraw health-information consent? Chat and health records will be locked until consent is renewed."
            )
        )
            return;

        setConsentSubmitting(true);
        try {
            await api.post("/consent", {
                consent_type: "health_information",
                consent_version: "1.0",
                accepted: false,
            });
            setConsentState("required");
            setConversations([]);
            setMessages([]);
            setActiveId(null);
            setConditions([]);
            setMedications([]);
            setTreatments([]);
        } catch (err: any) {
            alert(err.response?.data?.detail || "Unable to withdraw consent right now.");
        } finally {
            setConsentSubmitting(false);
        }
    }

    // Authentication Handlers
    async function handleLogin(emailVal: string, passVal: string) {
        setAuthLoading(true);
        setAuthError("");
        try {
            const response = await api.post("/auth/login", {
                email: emailVal,
                password: passVal,
            });
            localStorage.setItem("access_token", response.data.access_token);
            setIsAuthModalOpen(false);
            await loadUser();
        } catch (err: any) {
            setAuthError(err.response?.data?.detail || "Invalid email or password.");
        } finally {
            setAuthLoading(false);
        }
    }

    async function handleRegister(nameVal: string, emailVal: string, passVal: string) {
        setAuthLoading(true);
        setAuthError("");
        try {
            await api.post("/auth/register", {
                full_name: nameVal,
                email: emailVal,
                password: passVal,
            });
            // Automatically log in after registration
            const response = await api.post("/auth/login", {
                email: emailVal,
                password: passVal,
            });
            localStorage.setItem("access_token", response.data.access_token);
            setIsAuthModalOpen(false);
            await loadUser();
        } catch (err: any) {
            setAuthError(err.response?.data?.detail || "Registration failed. Please check your credentials.");
        } finally {
            setAuthLoading(false);
        }
    }

    function handleLogout() {
        localStorage.removeItem("access_token");
        setUser(null);
        setConversations([]);
        setMessages([]);
        setActiveId(null);
        setActiveView("chat");
        setConsentState("required");
    }

    // Conversation Management
    async function loadConversations() {
        try {
            const response = await api.get("/conversations");
            setConversations(response.data);
            if (response.data.length > 0 && !activeId) {
                // Open first conversation
                await openConversation(response.data[0].id);
            }
        } catch {
            // New user or no conversations
        }
    }

    async function createConversation() {
        setConversationLoading(true);
        setChatError("");
        try {
            setActiveView("chat");
            const response = await api.post("/conversations", {
                title: "New consultation",
            });
            const newConv = response.data;
            setConversations((prev) => [newConv, ...prev]);
            setActiveId(newConv.id);
            setMessages([]);
        } catch {
            setChatError("Unable to create a new conversation.");
        } finally {
            setConversationLoading(false);
        }
    }

    async function openConversation(id: number) {
        setConversationLoading(true);
        setChatError("");
        try {
            setActiveView("chat");
            setActiveId(id);
            const response = await api.get(`/conversations/${id}/messages`);
            setMessages(response.data);
        } catch {
            setChatError("Unable to load messages for this conversation.");
        } finally {
            setConversationLoading(false);
        }
    }

    async function deleteConversation(id: number) {
        if (!window.confirm("Permanently delete this consultation and all its messages?")) return;
        try {
            await api.delete(`/conversations/${id}`);
            setConversations((prev) => prev.filter((item) => item.id !== id));
            if (activeId === id) {
                setActiveId(null);
                setMessages([]);
            }
        } catch {
            setChatError("Unable to delete conversation.");
        }
    }

    async function renameConversation(id: number, newTitle: string) {
        try {
            const response = await api.patch(`/conversations/${id}`, { title: newTitle });
            setConversations((prev) =>
                prev.map((c) => (c.id === id ? { ...c, title: response.data.title } : c))
            );
        } catch {
            setChatError("Unable to rename conversation.");
        }
    }

    // Send Message
    async function handleSendMessage(
        content: string,
        attachmentText?: string,
        imagePreviewUrl?: string
    ) {
        let currentConvId = activeId;

        // Auto create conversation if none active
        if (!currentConvId) {
            try {
                const convRes = await api.post("/conversations", {
                    title: content.slice(0, 35) + "...",
                });
                currentConvId = convRes.data.id;
                setActiveId(currentConvId);
                setConversations((prev) => [convRes.data, ...prev]);
            } catch {
                setChatError("Could not initialize conversation.");
                return;
            }
        }

        // Optimistically add user message to list
        const tempUserMsg: Message = {
            id: Date.now(),
            role: "user",
            content,
            image_preview_url: imagePreviewUrl,
            attachment_name: attachmentText ? "Document attached" : undefined,
            created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, tempUserMsg]);
        setChatLoading(true);
        setChatError("");

        // Initialize AbortController for cancellation
        const controller = new AbortController();
        chatAbortControllerRef.current = controller;

        try {
            const payload: any = { content };
            if (attachmentText && attachmentText.trim()) {
                payload.attachment_text = attachmentText.trim();
            }

            const response = await api.post(
                `/conversations/${currentConvId}/messages`,
                payload,
                { signal: controller.signal }
            );
            const { assistant_message, sources = [] } = response.data;

            // Replace optimistic with real response
            setMessages((prev) => [
                ...prev.slice(0, -1),
                { ...tempUserMsg, id: response.data.user_message.id },
                { ...assistant_message, sources },
            ]);

            // Update conversation list updated_at
            void loadConversations();
        } catch (err: any) {
            // If the user aborted the request via Stop Agent, do not display error
            if (
                err?.name === "CanceledError" ||
                err?.code === "ERR_CANCELED" ||
                err?.message?.includes("canceled")
            ) {
                return;
            }
            setChatError(
                err.response?.data?.detail ||
                    "MediAssist is temporarily unable to generate a response. Please try again."
            );
        } finally {
            setChatLoading(false);
            chatAbortControllerRef.current = null;
        }
    }

    // Stop Agent Handler: Aborts in-flight response generation
    function handleStopAgent() {
        if (chatAbortControllerRef.current) {
            chatAbortControllerRef.current.abort();
            chatAbortControllerRef.current = null;
        }
        setChatLoading(false);
        setMessages((prev) => [
            ...prev,
            {
                id: Date.now(),
                role: "assistant",
                content: "⏹️ *Response generation stopped by user.*",
                created_at: new Date().toISOString(),
            },
        ]);
    }

    // Cancel Document Extraction Handler
    function handleCancelDocument() {
        if (docAbortControllerRef.current) {
            docAbortControllerRef.current.abort();
            docAbortControllerRef.current = null;
        }
        setDocumentLoading(false);
        setDocumentError("");
    }

    // Document & Image Extraction
    async function handleExtractDocument(file: File): Promise<ExtractedDocument | null> {
        setDocumentLoading(true);
        setDocumentError("");
        const formData = new FormData();
        formData.append("file", file);

        const controller = new AbortController();
        docAbortControllerRef.current = controller;

        try {
            const response = await api.post("/documents/extract", formData, {
                headers: { "Content-Type": "multipart/form-data" },
                signal: controller.signal,
            });
            return response.data;
        } catch (err: any) {
            if (
                err?.name === "CanceledError" ||
                err?.code === "ERR_CANCELED" ||
                err?.message?.includes("canceled")
            ) {
                return null;
            }
            const errorMsg =
                err.response?.data?.detail ||
                "Could not extract information from this document. Please try a clearer image or PDF.";
            setDocumentError(errorMsg);
            return null;
        } finally {
            setDocumentLoading(false);
            docAbortControllerRef.current = null;
        }
    }

    // Health Records Data Management
    async function loadHealthData() {
        setHealthLoading(true);
        setHealthError("");
        setHealthMessage("");
        try {
            const [pRes, cRes, mRes, tRes] = await Promise.all([
                api.get("/health/profile"),
                api.get("/health/conditions"),
                api.get("/health/medications"),
                api.get("/health/treatments"),
            ]);
            setHealthProfile(pRes.data);
            setConditions(cRes.data);
            setMedications(mRes.data);
            setTreatments(tRes.data);
        } catch {
            setHealthError("Could not retrieve health profile records.");
        } finally {
            setHealthLoading(false);
        }
    }

    async function handleSaveProfile(
        dob: string | null,
        sex: string | null,
        notes: string | null
    ) {
        setHealthLoading(true);
        setHealthError("");
        setHealthMessage("");
        try {
            const res = await api.put("/health/profile", {
                date_of_birth: dob,
                biological_sex: sex,
                health_notes: notes,
            });
            setHealthProfile(res.data);
            setHealthMessage("Health demographics saved successfully.");
        } catch (err: any) {
            setHealthError(err.response?.data?.detail || "Could not update health profile.");
        } finally {
            setHealthLoading(false);
        }
    }

    async function handleAddCondition(
        name: string,
        status: string,
        diagnosedDate: string | null,
        notes: string | null
    ) {
        setHealthLoading(true);
        try {
            await api.post("/health/conditions", {
                condition_name: name,
                status,
                diagnosed_date: diagnosedDate,
                notes,
            });
            await loadHealthData();
            setHealthMessage("Condition added to your medical profile.");
        } catch (err: any) {
            setHealthError(err.response?.data?.detail || "Failed to add condition.");
        } finally {
            setHealthLoading(false);
        }
    }

    async function handleDeleteCondition(id: number) {
        if (!window.confirm("Remove this condition from your health profile?")) return;
        try {
            await api.delete(`/health/conditions/${id}`);
            await loadHealthData();
            setHealthMessage("Condition removed.");
        } catch {
            setHealthError("Unable to delete condition.");
        }
    }

    async function handleAddMedication(
        name: string,
        status: string,
        startDate: string | null,
        notes: string | null
    ) {
        setHealthLoading(true);
        try {
            await api.post("/health/medications", {
                medication_name: name,
                status,
                start_date: startDate,
                notes,
            });
            await loadHealthData();
            setHealthMessage("Medication saved to your profile.");
        } catch (err: any) {
            setHealthError(err.response?.data?.detail || "Failed to add medication.");
        } finally {
            setHealthLoading(false);
        }
    }

    async function handleDeleteMedication(id: number) {
        if (!window.confirm("Remove this medication from your health profile?")) return;
        try {
            await api.delete(`/health/medications/${id}`);
            await loadHealthData();
            setHealthMessage("Medication removed.");
        } catch {
            setHealthError("Unable to delete medication.");
        }
    }

    async function handleAddTreatment(
        name: string,
        type: string | null,
        status: string,
        startDate: string | null,
        notes: string | null
    ) {
        setHealthLoading(true);
        try {
            await api.post("/health/treatments", {
                treatment_name: name,
                treatment_type: type,
                status,
                start_date: startDate,
                notes,
            });
            await loadHealthData();
            setHealthMessage("Treatment record saved.");
        } catch (err: any) {
            setHealthError(err.response?.data?.detail || "Failed to add treatment.");
        } finally {
            setHealthLoading(false);
        }
    }

    async function handleDeleteTreatment(id: number) {
        if (!window.confirm("Remove this treatment record?")) return;
        try {
            await api.delete(`/health/treatments/${id}`);
            await loadHealthData();
            setHealthMessage("Treatment record removed.");
        } catch {
            setHealthError("Unable to delete treatment.");
        }
    }

    // Active conversation object
    const currentConversation = conversations.find((c) => c.id === activeId) || null;

    // View Routing: If not authenticated, render modern Landing Page + Auth Modal
    if (!user) {
        return (
            <div className="app-root">
                <LandingPage onOpenAuth={() => setIsAuthModalOpen(true)} />
                <AuthModal
                    isOpen={isAuthModalOpen}
                    onClose={() => setIsAuthModalOpen(false)}
                    onLogin={handleLogin}
                    onRegister={handleRegister}
                    loading={authLoading}
                    error={authError}
                />
            </div>
        );
    }

    // Consent gate: If health consent is required
    if (consentState !== "accepted") {
        return (
            <div className="app-root">
                <ConsentModal
                    consentState={consentState}
                    consentError={consentError}
                    consentSubmitting={consentSubmitting}
                    onAccept={acceptHealthConsent}
                    onWithdraw={withdrawHealthConsent}
                    onRetry={loadConsent}
                    onLogout={handleLogout}
                />
            </div>
        );
    }

    // Main App Shell
    return (
        <div className="app-layout">
            <Sidebar
                user={user}
                conversations={conversations}
                activeId={activeId}
                activeView={activeView}
                conversationLoading={conversationLoading}
                onSelectConversation={(id) => void openConversation(id)}
                onCreateConversation={() => void createConversation()}
                onDeleteConversation={(id) => void deleteConversation(id)}
                onRenameConversation={renameConversation}
                onSelectHealthView={() => {
                    setActiveView("health");
                    void loadHealthData();
                }}
                onLogout={handleLogout}
                onWithdrawConsent={() => void withdrawHealthConsent()}
                isMobileOpen={isMobileSidebarOpen}
                onCloseMobile={() => setIsMobileSidebarOpen(false)}
            />

            <div className="app-main-content">
                {activeView === "health" ? (
                    <HealthDashboard
                        user={user}
                        profile={healthProfile}
                        conditions={conditions}
                        medications={medications}
                        treatments={treatments}
                        loading={healthLoading}
                        message={healthMessage}
                        error={healthError}
                        onSaveProfile={handleSaveProfile}
                        onAddCondition={handleAddCondition}
                        onDeleteCondition={handleDeleteCondition}
                        onAddMedication={handleAddMedication}
                        onDeleteMedication={handleDeleteMedication}
                        onAddTreatment={handleAddTreatment}
                        onDeleteTreatment={handleDeleteTreatment}
                        onBackToChat={() => setActiveView("chat")}
                    />
                ) : (
                    <ChatArea
                        user={user}
                        activeConversation={currentConversation}
                        messages={messages}
                        loading={chatLoading}
                        conversationLoading={conversationLoading}
                        error={chatError}
                        onSendMessage={handleSendMessage}
                        onStopAgent={handleStopAgent}
                        onCancelDocument={handleCancelDocument}
                        onCreateConversation={() => void createConversation()}
                        onClearChat={() => {
                            if (window.confirm("Clear all messages in this conversation?")) {
                                setMessages([]);
                            }
                        }}
                        onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
                        onExtractDocument={handleExtractDocument}
                        documentLoading={documentLoading}
                        documentError={documentError}
                        setDocumentError={setDocumentError}
                    />
                )}
            </div>
        </div>
    );
}

export default App;
