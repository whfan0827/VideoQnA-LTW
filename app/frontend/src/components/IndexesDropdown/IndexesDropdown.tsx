import { Dropdown, IDropdownOption, IDropdownStyles } from "@fluentui/react/lib/Dropdown";

interface Props {
    indexes: IDropdownOption[];
    selectedIndex?: string;
    onIndexChanged: (index: string) => void;
}
const dropdownStyles: Partial<IDropdownStyles> = {
    dropdown: {}
};
export const IndexesDropdown = ({ indexes, selectedIndex, onIndexChanged }: Props) => {
    const onChange = (event: React.FormEvent<HTMLDivElement>, item: IDropdownOption | undefined): void => {
        if (item) {
            console.log("Dropdown onChange - selected item: ", item);
            onIndexChanged(item.key as string);
        }
    };
    
    // 添加調試信息
    console.log("IndexesDropdown render - selectedIndex: ", selectedIndex);
    console.log("IndexesDropdown render - indexes: ", indexes);
    
    return (
        <div>
            <Dropdown 
                label="Video Library" 
                placeholder="Select video library" 
                options={indexes} 
                styles={dropdownStyles} 
                onChange={onChange} 
                selectedKey={selectedIndex}
            />
        </div>
    );
};
