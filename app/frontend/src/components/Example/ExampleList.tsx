import { useState, useEffect } from "react";
import { Example } from "./Example";
import { useAppConfig } from "../../hooks/useAppConfig";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const DEFAULT_EXAMPLES: ExampleModel[] = [
    {
        text: "What insights are included with Azure AI Video Indexer?",
        value: "What insights are included with Azure AI Video Indexer?"
    },
    {
        text: "What is OCR?",
        value: "What is OCR?"
    },
    {
        text: "What is the distance to Mars?",
        value: "What is the distance to Mars?"
    }
];



interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    const { targetLibrary } = useAppConfig();
    const [examples, setExamples] = useState<ExampleModel[]>(DEFAULT_EXAMPLES);
    
    console.log('🔍 ExampleList render:', { targetLibrary });

    // Load custom starters from localStorage (fallback)
    const loadCustomStarters = () => {
        try {
            const saved = localStorage.getItem('conversation_starters');
            if (saved) {
                const customStarters = JSON.parse(saved) as ExampleModel[];
                if (customStarters.length > 0) {
                    setExamples(customStarters);
                    return;
                }
            }
        } catch (error) {
            console.error('Error loading custom starters:', error);
        }
        setExamples(DEFAULT_EXAMPLES);
    };

    // Load library-specific starters
    const loadLibraryStarters = async (libraryId: string) => {
        try {
            // First try to load from cache
            const cached = getLibraryStartersFromCache(libraryId);
            if (cached) {
                setExamples(cached);
                return;
            }

            // Load from API
            const response = await fetch(`/api/libraries/${libraryId}/conversation-starters`);
            if (response.ok) {
                const data = await response.json();
                const starters = data.starters || DEFAULT_EXAMPLES;
                setExamples(starters);
                saveLibraryStartersToCache(libraryId, starters);
            } else {
                throw new Error('Failed to load library starters');
            }
        } catch (error) {
            console.error('Error loading library conversation starters:', error);
            // Fall back to global localStorage starters
            loadCustomStarters();
        }
    };

    // Cache management functions
    const getLibraryStartersFromCache = (libraryId: string): ExampleModel[] | null => {
        try {
            const cached = localStorage.getItem('library_conversation_starters');
            if (cached) {
                const libraryStarters = JSON.parse(cached);
                return libraryStarters[libraryId] || null;
            }
        } catch (error) {
            console.error('Error reading from cache:', error);
        }
        return null;
    };

    const saveLibraryStartersToCache = (libraryId: string, starters: ExampleModel[]) => {
        try {
            const existingCache = localStorage.getItem('library_conversation_starters');
            const libraryStarters = existingCache ? JSON.parse(existingCache) : {};
            libraryStarters[libraryId] = starters;
            localStorage.setItem('library_conversation_starters', JSON.stringify(libraryStarters));
        } catch (error) {
            console.error('Error saving to cache:', error);
        }
    };

    // Load starters when targetLibrary changes or component mounts
    useEffect(() => {
        console.log('🔍 ExampleList: targetLibrary effect triggered:', { targetLibrary });
        
        if (targetLibrary) {
            loadLibraryStarters(targetLibrary);
        } else {
            loadCustomStarters();
        }
    }, [targetLibrary]);

    useEffect(() => {
        // Listen for updates from ConversationSettings - reload current library starters
        const handleUpdate = () => {
            if (targetLibrary) {
                console.log('🔍 ExampleList: Conversation starters updated, reloading library starters for:', targetLibrary);
                loadLibraryStarters(targetLibrary);
            } else {
                console.log('🔍 ExampleList: Conversation starters updated, loading default starters');
                loadCustomStarters();
            }
        };

        // Listen for target library changes (legacy support)
        const handleTargetLibraryChange = (event: any) => {
            const { libraryId } = event.detail || {};
            if (libraryId) {
                loadLibraryStarters(libraryId);
            } else {
                loadCustomStarters();
            }
        };

        window.addEventListener('conversation_starters_updated', handleUpdate);
        window.addEventListener('target_library_changed', handleTargetLibraryChange);
        
        return () => {
            window.removeEventListener('conversation_starters_updated', handleUpdate);
            window.removeEventListener('target_library_changed', handleTargetLibraryChange);
        };
    }, [targetLibrary]); // Include targetLibrary in dependencies

    return (
        <ul className={styles.examplesNavList}>
            {examples.map((x, i) => (
                <li className={styles.examplesNavListItem} key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};