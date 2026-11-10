import React, { useState } from "react";
import {
    Activity,
    Check,
    Edit2,
    HeartPulse,
    LogOut,
    MessageSquare,
    Plus,
    Search,
    Shield,
    Trash2,
    X,
} from "lucide-react";
import type { Conversation, User } from "../types";

interface SidebarProps {
    user: User;
    conversations: Conversation[];
    activeId: number | null;
    activeView: "chat" | "health";
    conversationLoading: boolean;
    onSelectConversation: (id: number) => void;
    onCreateConversation: () => void;
    onDeleteConversation: (id: number) => void;
    onRenameConversation: (id: number, newTitle: string) => Promise<void>;
    onSelectHealthView: () => void;
    onLogout: () => void;
    onWithdrawConsent: () => void;
    isMobileOpen: boolean;
    onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
    user,
    conversations,
    activeId,
    activeView,
    conversationLoading,
    onSelectConversation,
    onCreateConversation,
    onDeleteConversation,
    onRenameConversation,
    onSelectHealthView,
    onLogout,
    onWithdrawConsent,
    isMobileOpen,
    onCloseMobile,
}) => {
    const [searchQuery, setSearchQuery] = useState("");
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editTitle, setEditTitle] = useState("");

    const filteredConversations = conversations.filter((c) =>
        c.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const startEditing = (c: Conversation, e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingId(c.id);
        setEditTitle(c.title);
    };

    const saveEditing = async (id: number, e: React.FormEvent) => {
        e.preventDefault();
        if (editTitle.trim()) {
            await onRenameConversation(id, editTitle.trim());
        }
        setEditingId(null);
    };

    const cancelEditing = (e: React.MouseEvent) => {
        e.stopPropagation();
        setEditingId(null);
    };

    return (
        <>
            {isMobileOpen && (
                <div
                    className="sidebar-backdrop"
                    onClick={onCloseMobile}
                    aria-hidden="true"
                />
            )}
            <aside className={`app-sidebar ${isMobileOpen ? "mobile-open" : ""}`}>
                {/* Brand Header */}
                <div className="sidebar-brand-wrapper">
                    <div className="sidebar-brand">
                        <div className="brand-icon-box">
                            <HeartPulse size={20} className="text-emerald-500" />
                        </div>
                        <span className="brand-title">MediAssist</span>
                    </div>
                    {isMobileOpen && (
                        <button
                            type="button"
                            className="mobile-close-btn"
                            onClick={onCloseMobile}
                            aria-label="Close menu"
                        >
                            <X size={18} />
                        </button>
                    )}
                </div>

                {/* Main Actions */}
                <div className="sidebar-actions">
                    <button
                        type="button"
                        className="btn btn-primary btn-new-chat"
                        onClick={() => {
                            onCreateConversation();
                            if (isMobileOpen) onCloseMobile();
                        }}
                        disabled={conversationLoading}
                    >
                        <Plus size={18} />
                        <span>{conversationLoading ? "Creating..." : "New Chat"}</span>
                    </button>

                    <button
                        type="button"
                        className={`sidebar-nav-item ${activeView === "health" ? "active" : ""}`}
                        onClick={() => {
                            onSelectHealthView();
                            if (isMobileOpen) onCloseMobile();
                        }}
                    >
                        <Activity size={18} className="text-emerald-500" />
                        <span>My Health Profile</span>
                    </button>
                </div>

                {/* Search Conversations */}
                <div className="sidebar-search">
                    <Search size={14} className="search-icon" />
                    <input
                        type="text"
                        placeholder="Search chats..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                        <button
                            type="button"
                            className="search-clear"
                            onClick={() => setSearchQuery("")}
                        >
                            <X size={12} />
                        </button>
                    )}
                </div>

                {/* Conversation List */}
                <div className="sidebar-conversation-section">
                    <div className="section-label">
                        <span>Recent Conversations</span>
                        <span className="count-badge">{filteredConversations.length}</span>
                    </div>

                    <div className="conversation-list">
                        {filteredConversations.length === 0 ? (
                            <p className="empty-conv-text">
                                {searchQuery ? "No matching chats found." : "No conversations yet."}
                            </p>
                        ) : (
                            filteredConversations.map((c) => {
                                const isActive = activeView === "chat" && activeId === c.id;
                                const isEditing = editingId === c.id;

                                return (
                                    <div
                                        key={c.id}
                                        className={`conv-item-wrapper ${isActive ? "active" : ""}`}
                                        onClick={() => {
                                            if (!isEditing) {
                                                onSelectConversation(c.id);
                                                if (isMobileOpen) onCloseMobile();
                                            }
                                        }}
                                    >
                                        <MessageSquare size={16} className="conv-icon" />

                                        {isEditing ? (
                                            <form
                                                onSubmit={(e) => saveEditing(c.id, e)}
                                                className="conv-edit-form"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                <input
                                                    type="text"
                                                    value={editTitle}
                                                    onChange={(e) => setEditTitle(e.target.value)}
                                                    autoFocus
                                                    maxLength={60}
                                                />
                                                <button type="submit" className="conv-action-btn check">
                                                    <Check size={14} />
                                                </button>
                                                <button
                                                    type="button"
                                                    className="conv-action-btn cancel"
                                                    onClick={cancelEditing}
                                                >
                                                    <X size={14} />
                                                </button>
                                            </form>
                                        ) : (
                                            <>
                                                <span className="conv-title" title={c.title}>
                                                    {c.title}
                                                </span>
                                                <div className="conv-actions">
                                                    <button
                                                        type="button"
                                                        className="conv-action-btn"
                                                        title="Rename"
                                                        onClick={(e) => startEditing(c, e)}
                                                    >
                                                        <Edit2 size={13} />
                                                    </button>
                                                    <button
                                                        type="button"
                                                        className="conv-action-btn delete"
                                                        title="Delete"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            onDeleteConversation(c.id);
                                                        }}
                                                    >
                                                        <Trash2 size={13} />
                                                    </button>
                                                </div>
                                            </>
                                        )}
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* Footer User Profile & Consent */}
                <div className="sidebar-footer">
                    <div className="user-profile-card">
                        <div className="user-avatar">
                            {user.full_name
                                ? user.full_name.slice(0, 2).toUpperCase()
                                : "MA"}
                        </div>
                        <div className="user-info">
                            <span className="user-name" title={user.full_name}>
                                {user.full_name}
                            </span>
                            <span className="user-email" title={user.email}>
                                {user.email}
                            </span>
                        </div>
                        <button
                            type="button"
                            className="logout-btn"
                            onClick={onLogout}
                            title="Sign Out"
                            aria-label="Sign Out"
                        >
                            <LogOut size={16} />
                        </button>
                    </div>

                    <div className="consent-footer-action">
                        <Shield size={12} className="text-emerald-500" />
                        <span>Health Data Consent Active</span>
                        <button
                            type="button"
                            className="consent-withdraw-link"
                            onClick={onWithdrawConsent}
                            title="Withdraw Consent"
                        >
                            Withdraw
                        </button>
                    </div>
                </div>
            </aside>
        </>
    );
};
