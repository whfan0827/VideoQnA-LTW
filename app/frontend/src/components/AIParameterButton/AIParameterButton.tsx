import { Text } from "@fluentui/react";
import { Settings20Regular } from "@fluentui/react-icons";

import styles from "./AIParameterButton.module.css";

interface Props {
    className?: string;
    onClick: () => void;
}

export const AIParameterButton = ({ className, onClick }: Props) => {
    return (
        <div className={`${styles.container} ${className ?? ""}`} onClick={onClick}>
            <Settings20Regular />
            <Text>AI Parameters</Text>
        </div>
    );
};
