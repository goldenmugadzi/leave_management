import { useCallback, useRef, useEffect, useState } from 'react';
import { useScheduleContext } from '../context/ScheduleContext';
import { ICommittee } from '../types/scheduleTypes';

const COMMITTEE_STORAGE_KEY = 'committee_members_cache';

export const useCommitteeState = () => {
  const { committee: contextCommittee, setCommittee: setContextCommittee } = useScheduleContext();
  const [localCommitteeMembers, setLocalCommitteeMembers] = useState<ICommittee[]>([]);
  const lastUpdateRef = useRef<{ members: ICommittee[], timestamp: number } | null>(null);
  const isInitializedRef = useRef(false);
  const isLoadingFromStorageRef = useRef(false);

  // Load committee data from sessionStorage on mount (only once)
  useEffect(() => {
    if (isLoadingFromStorageRef.current) return;
    isLoadingFromStorageRef.current = true;
    
    try {
      const stored = sessionStorage.getItem(COMMITTEE_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          console.log("🔍 useCommitteeState - Loading from sessionStorage:", parsed.length, "members");
          setLocalCommitteeMembers(parsed);
          setContextCommittee(parsed);
          isInitializedRef.current = true;
        }
      }
    } catch (error) {
      console.error("❌ useCommitteeState - Error loading from sessionStorage:", error);
    }
  }, [setContextCommittee]);

  // Initialize local state from context if available (only when context has data and we haven't initialized)
  useEffect(() => {
    if (contextCommittee.length > 0 && !isInitializedRef.current && !isLoadingFromStorageRef.current) {
      console.log("🔍 useCommitteeState - Initializing from context:", contextCommittee.length, "members");
      setLocalCommitteeMembers(contextCommittee);
      isInitializedRef.current = true;
      
      // Also save to sessionStorage
      try {
        sessionStorage.setItem(COMMITTEE_STORAGE_KEY, JSON.stringify(contextCommittee));
      } catch (error) {
        console.error("❌ useCommitteeState - Error saving to sessionStorage:", error);
      }
    }
  }, [contextCommittee]);

  // Update context state with additional safety checks
  const updateCommitteeMembers = useCallback((members: ICommittee[]) => {
    console.log("🔍 useCommitteeState - Updating committee members:", members.length, "members");
    
    // Validate the members data
    if (!Array.isArray(members)) {
      console.error("❌ useCommitteeState - Invalid members data (not an array):", members);
      return;
    }
    
    // Store the update for debugging
    lastUpdateRef.current = {
      members,
      timestamp: Date.now()
    };
    
    // Update both local and context state
    setLocalCommitteeMembers(members);
    setContextCommittee(members);
    
    // Save to sessionStorage for persistence
    try {
      sessionStorage.setItem(COMMITTEE_STORAGE_KEY, JSON.stringify(members));
      console.log("🔍 useCommitteeState - Saved to sessionStorage");
    } catch (error) {
      console.error("❌ useCommitteeState - Error saving to sessionStorage:", error);
    }
    
    console.log("🔍 useCommitteeState - Context and local update initiated");
  }, [setContextCommittee]);

  // Clear committee cache
  const clearCommitteeCache = useCallback(() => {
    console.log("🔍 useCommitteeState - Clearing committee cache");
    setLocalCommitteeMembers([]);
    setContextCommittee([]);
    isInitializedRef.current = false;
    isLoadingFromStorageRef.current = false;
    try {
      sessionStorage.removeItem(COMMITTEE_STORAGE_KEY);
      console.log("🔍 useCommitteeState - Cleared from sessionStorage");
    } catch (error) {
      console.error("❌ useCommitteeState - Error clearing from sessionStorage:", error);
    }
  }, [setContextCommittee]);

  // Get the current committee members (prefer context, fallback to local)
  const committeeMembers = contextCommittee.length > 0 ? contextCommittee : localCommitteeMembers;

  // Debug effect to track context changes (only log, don't trigger updates)
  useEffect(() => {
    if (contextCommittee.length > 0 || localCommitteeMembers.length > 0) {
      console.log("🔍 useCommitteeState - Context committee changed:", {
        length: contextCommittee.length,
        lastUpdate: lastUpdateRef.current
      });
    }
  }, [contextCommittee]);

  // Only log state changes occasionally to avoid spam
  const logState = useCallback(() => {
    // Only log if there are committee members to avoid spam
    if (committeeMembers.length > 0) {
      console.log("🔍 useCommitteeState - Current committee state:", {
        contextCommitteeLength: contextCommittee.length,
        localCommitteeMembersLength: localCommitteeMembers.length,
        finalCommitteeMembersLength: committeeMembers.length,
        isInitialized: isInitializedRef.current,
        isLoadingFromStorage: isLoadingFromStorageRef.current
      });
    }
  }, [contextCommittee.length, localCommitteeMembers.length, committeeMembers.length]);

  // Log state changes less frequently
  useEffect(() => {
    const timeoutId = setTimeout(logState, 500); // Increased delay to reduce spam
    return () => clearTimeout(timeoutId);
  }, [logState]);

  return {
    committeeMembers,
    updateCommitteeMembers,
    clearCommitteeCache
  };
}; 