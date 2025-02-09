import unrealsdk
import os
import json
from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, RegisterMod, SDKMod, Options, Hook, Game
from typing import cast

from unrealsdk import FindObject, UObject, GetEngine

class anarchystacks(SDKMod):
    # need to add the option to keep anarchy when dying
    #  maybe not dont know if that would be to overpowered 
    # TODO add Co-OP
    Name: str = "KeepAnarchy"
    Author: str = "Sampletext282" # i also want to apoligize for my awful code :)
    Description: str = ("Lets you keep a self set percentage of your Anarchy stacks on Savequit. Does not work in Co-op")
    Version: str = "0.9"
    Types: ModTypes = ModTypes.Utility
    SupportedGames: Game = Game.BL2
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings
    
    PercentSlider: Options.Slider
    Threshold: Options.Slider
    def __init__(self):
        self.PercentSlider = Options.Slider(
        Caption = "Keep%",
        Description = "The Percentage of Anarchy stacks you keep.",
        StartingValue = 50,
        MinValue = 0,
        MaxValue = 100,
        Increment = 1
        )
        self.Threshold = Options.Slider(
        Caption = "Threshold",
        Description = "Anarchy stacks won't go below this Value.",
        StartingValue = 0,
        MinValue = 0,
        MaxValue = 600,
        Increment = 1
        )
        self.Options = [self.PercentSlider, self.Threshold]
        self.firstime = True 
        self.path = os.getcwd() + r"/Mods/KeepAnarchy/saved_stacks.json" # path to the .json file
        self.savefile = ""
        
    def get_anarchy_stacks(self) -> int: 
        """Get stacks of anarchy from the attribute definition.""" # FindObject from Justin99's Speedrun Practice Mod https://github.com/Justin99x/bl-sdk-mods/tree/main/SpeedrunPractice
        current_anarchy = FindObject("DesignerAttributeDefinition", "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks").GetValue(cast(UObject, GetEngine().GamePlayers[0].Actor))
        return int(current_anarchy[0])
        
    def get_max_anarchy_stacks(self) -> int:
        """returns the maximum stacks of Anarchy the player can have""" # FindObject from Justin99's Speedrun Practice Mod https://github.com/Justin99x/bl-sdk-mods/tree/main/SpeedrunPractice
        max_anarchy = FindObject("DesignerAttributeDefinition", "GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_StackCap").GetValue(cast(UObject, GetEngine().GamePlayers[0].Actor))
        return int(max_anarchy[0])
    
    def set_anarchy_stacks(self, target_stacks) -> None: 
        """Set anarchy stacks to desired value""" # FindObject from Justin99's Speedrun Practice Mod https://github.com/Justin99x/bl-sdk-mods/tree/main/SpeedrunPractice
        AnarchyAttribute = FindObject('DesignerAttributeDefinition', 'GD_Tulip_Mechromancer_Skills.Misc.Att_Anarchy_NumberOfStacks')
        InstancedAnarachy = GetEngine().GamePlayers[0].Actor.Pawn.GetInstancedDesignerAttribute(AnarchyAttribute)
        InstancedAnarachy.SetBaseValue((target_stacks, None, None, 1), GetEngine().GamePlayers[0].Actor.Pawn)
        return
        
    def get_data(self) -> dict:
        """returns the stacks of Anarchy saved in the .json file"""
        with open(self.path) as json_data:
            data = json.load(json_data)
        return data
    
    def dump_data(self, data) -> None:
        """saves the stacks of Anarchy to the .json file"""
        with open(self.path, 'w', encoding='utf-8') as json_data:
            json.dump(data, json_data, ensure_ascii=False, indent=4)
        return
    
    def save_anarchy_stacks(self) -> int:
        """Saves the current Anarchy to a .json file"""
        # TODO still attemps to save Anarchy even if the player isn't Gaige
        current_anarchy = self.get_anarchy_stacks()
        if current_anarchy != 0:
            #Log("current anarchy is not zero")
            stacks = self.get_data()
            stacks[self.savefile] = str(current_anarchy)
            self.dump_data(stacks)
        return
        
    def retrive_anarchy_stacks(self) -> int:
        """Sets the current Anarchy to the Value corresponding to the savefile name.sav that is saved in the .json while considering the threshold and percentage"""
        max_anarchy = self.get_max_anarchy_stacks()
        stacks = self.get_data()
        if self.savefile in stacks:
            #Log(".sav found in the .json")
            anarchy_stacks = stacks[self.savefile]
            anarchy_stacks = int(anarchy_stacks)
            if (anarchy_stacks*self.PercentSlider.CurrentValue // 100) >= self.Threshold.CurrentValue:
                self.set_anarchy_stacks(min(max_anarchy, anarchy_stacks*self.PercentSlider.CurrentValue // 100))
            else:
                self.set_anarchy_stacks(min(max_anarchy, anarchy_stacks, self.Threshold.CurrentValue))
            stacks.pop(self.savefile)
            self.dump_data(stacks)
        else:
            #Log(".sav not found in the .json")
            return
    
    """Hooks that are used to determine when the player spawned for the first time after save quiting"""
    # doing it this way: First Hook triggers to early if you set the stacks there, they would get deleted when the spawning is finished
    # Second Hook triggers to often to be used only on first spawning
    @Hook("WillowGame.PlayerSkillTree.Initialize") # Hook and caller from LaryIsland's Melee Enhanced mod https://github.com/LaryIsland/bl-sdk-mods/tree/main/MeleeEnhancement
    def InjectSkillChanges(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:  
        if caller.Outer.PlayerClass.CharacterNameId.CharacterClassId.ClassName == "Mechromancer": # checks if the player is gaige
            #Log("Player is Gaige")
            self.firstime = True
        return True
    @Hook("WillowGame.WillowPlayerController.SaveGame") 
    def Spawned(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if self.firstime: 
            self.savefile = cast(UObject, GetEngine().GamePlayers[0].Actor).GetWillowGlobals().GetWillowSaveGameManager().LastLoadedFilePath # cast is the savefile name.sav || cast from Justin99's Speedrun Practice Mod https://github.com/Justin99x/bl-sdk-mods/tree/main/SpeedrunPractice
            ("retriving anarchy stacks")
            self.retrive_anarchy_stacks()
            self.firstime = False
        return True
        
    """Hook for detecting savequit and saving the Anarchystacks before"""
    @Hook("WillowGame.WillowPlayerController.ReturnToTitleScreen")
    def onExit(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        #Log("saving anarchy stacks")
        self.save_anarchy_stacks()
        return True
        
instance = anarchystacks()

if __name__ == "__main__":
    #Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            #Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break

RegisterMod(instance)
