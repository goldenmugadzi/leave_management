from typing import Protocol, Dict
from django.core.files.uploadedfile import UploadedFile
from pandas import DataFrame
import pandas as pd

class FileHandlerStrategyInterface(Protocol):
    def get_data(self, file: UploadedFile)->Dict[str, pd.DataFrame]:
        """Handler for reading files to memory

        Args:
            file (UploadedFile): file or dir

        Returns:
            dict: Prepared data
        """
        pass

class UserQualificationStrategy:
    
    def __load_all_sheets(self):
        return pd.read_excel(self.file, sheet_name=None, header=None)
    
    def __get_index_of_table_header(self, df: DataFrame):
        header_row_index = None
        for i, row in df.iterrows():
            row_lower = [str(val).strip().lower() for val in row.values if pd.notna(val)]
            if "surname" in row_lower:
                header_row_index = i
                break
        return header_row_index
    
    def __reload_data_cleaned(self, sheet_name: str, header: int):
        df = pd.read_excel(self.file, sheet_name=sheet_name, header=[header, header + 1])
        
        # Drop empty rows
        df = df.dropna(how="all").reset_index(drop=True)
        return df
    
    def __get_tables_data(self):
        merged_tables = []
        all_sheets_data = self.__load_all_sheets()
        for sheet_name, df_raw in all_sheets_data.items():
            table_header_index = self.__get_index_of_table_header(df_raw)
            
            if table_header_index is None:
                raise ValueError(f"[UserQualificationStrategy] Could not find header row in sheet: {sheet_name}")
            
            df = self.__reload_data_cleaned(sheet_name=sheet_name, header=table_header_index)
            
            # Flatten MultiIndex column headers
            df.columns = [
                " ".join([str(c) for c in col if str(c) != "nan"]).strip()
                if isinstance(col, tuple) else str(col).strip()
                for col in df.columns
            ]
            merged_tables.append(df)
        return merged_tables
    
    def __merged_tables(self)->pd.DataFrame:
        tables_data = self.__get_tables_data()
        merged_df = pd.concat(tables_data, ignore_index=True)
        return merged_df

    def get_data(self, file: UploadedFile)->Dict[str, pd.DataFrame]:
        """
        Reads an Excel file with multiple sheets, detects the header row dynamically,
        and returns a dict of DataFrames keyed by sheet name.
        """
        self.file = file
        return self.__merged_tables()
    
class FileHandlerStrategyContext:
    def __init__(self, strategy: FileHandlerStrategyInterface):
        self.strategy = strategy
        
    def data(self, file: UploadedFile)->DataFrame:
        try:
            return self.strategy.get_data(file=file)
        except Exception as e:
            raise Exception(f"[FileHandlerStrategyContext] {self.strategy}, failed with error: {e}")