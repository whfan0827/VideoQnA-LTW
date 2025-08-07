import { Text } from "@fluentui/react";
import { Chat24Regular } from "@fluentui/react-icons";

import styles from "./SettingsButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
}

export const SettingsButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Chat24Regular />
            <Text>{"Conversation settings"}</Text>
        </div>
    );
};
