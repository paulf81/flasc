# Wrap the table analysis class in an outer class which performs bootstrapping

import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from flasc.table_analysis import TableAnalysis


# np.random.seed(0)

# NOTE WE TOOK THE DECISION THAT BOOTSTRAPPING WILL BE ONLY FOR COMPARING TWO CASES

class TableAnalysisBootstrap():

    def __init__(self, 
                    wd_edges = np.arange(0,  360 + 2.0, 2.0),
                    ws_edges = np.arange(0 - 0.5, 50, 1.0),
                    pow_ref_edges = np.arange(0,  15000 + 100.0, 100.0), #kW
                    use_pow_ref = False,
                    minutes_per_point=10.0,
    ):        
        
        # Check that the inputs are valid 
        if len(ws_edges) < 2:
            raise ValueError("ws_edges must have at least 2 elements")
        if len(wd_edges) < 2:
            raise ValueError("wd_edges must have at least 2 elements")
        if len(pow_ref_edges) < 2:
            raise ValueError("pow_ref_edges must have at least 2 elements")
        
        # Save the inputs
        self.ws_edges = ws_edges
        self.wd_edges = wd_edges
        self.pow_ref_edges = pow_ref_edges
        self.use_pow_ref = use_pow_ref
        self.minutes_per_point = minutes_per_point
        
        # Initialize user_defined_frequency_matrix to None
        self.user_defined_frequency_matrix = None
        
        # Initialize the number of cases to 0
        self.n_cases = 0

        # Initialize df list
        self.case_df_list = []
        self.case_names = []

        # Initialize the list of tables
        self.nominal_table = None
        self.bootstrap_tables = None

    def add_df(self, case_df, case_name, seaborn_color_palette='colorblind'):

        df = case_df.copy()

        # Add df and case_name to the list
        self.case_df_list.append(df)
        self.case_names.append(case_name)
        self.n_cases += 1

        # Update the color pallette for plotting
        # self.case_colors = sns.color_palette(seaborn_color_palette, self.n_cases)


    def build_bootstrap_tables(self,
                n_bootstraps = 20,
                n_blocks = 10,):
        
        # Make sure there are two cases
        if self.n_cases != 2:
            raise ValueError("There must be two cases to perform bootstrapping")

        # Make sure the number of bootstraps is an integer
        if not isinstance(n_bootstraps, int):
            raise TypeError("n_bootstraps must be an integer")
        
        # Make sure the number of blocks is an integer
        if not isinstance(n_blocks, int):
            raise TypeError("n_blocks must be an integer")

        # Save the number of bootstraps and blocks
        self.n_bootstraps = n_bootstraps
        self.n_blocks = n_blocks

        # Build the nomiminal table
        self.nominal_table = TableAnalysis(wd_edges=self.wd_edges, 
                                            ws_edges=self.ws_edges, 
                                            pow_ref_edges=self.pow_ref_edges,
                                            use_pow_ref=self.use_pow_ref,
                                            minutes_per_point = self.minutes_per_point)
        for c_i in range(self.n_cases):
            self.nominal_table.add_df(self.case_df_list[c_i], self.case_names[c_i])

        # Break the dataframes in self.case_df_list into n_blocks dataframes
        block_data_frame_list = []

        for df in self.case_df_list:
                
                num_rows = df.shape[0]
                
                # Declare a vector of blocks whose length is equal to df.shape[0] and whose values are 0,1,...,n_blocks-1
                
                blocks = np.repeat(np.arange(self.n_blocks), np.ceil(num_rows / self.n_blocks).astype(int))[:num_rows]

                # Add blocks as a column to the dataframe
                df['block'] = blocks
    
                # Split the dataframe into n_blocks dataframes
                df_blocks = [df[df['block'] == b_i].drop('block',axis=1) for b_i in range(self.n_blocks)]

                block_data_frame_list.append(df_blocks)


        # Intialize a list of tables whose dimensions are n_bootstraps
        self.bootstrap_tables = np.zeros(self.n_bootstraps, dtype=object)

        df_list = np.zeros([self.n_cases, self.n_bootstraps], dtype=object)

        # Get a list of table_analysis from n_bootstraps resamplings of the dataframe
        for b_i in range(self.n_bootstraps):
            sampled_blocks = np.random.choice(list(range(self.n_blocks)), size=self.n_blocks, replace=True)
            
            # Create a table analysis object
            table_analysis = TableAnalysis(wd_edges=self.wd_edges, 
                                            ws_edges=self.ws_edges, 
                                            pow_ref_edges=self.pow_ref_edges,
                                            use_pow_ref=self.use_pow_ref,
                                            minutes_per_point = self.minutes_per_point)

            for c_i in range(self.n_cases):
                df_sampled = pd.concat([block_data_frame_list[c_i][sb_i] for sb_i in sampled_blocks])

                df_list[c_i, b_i] = df_sampled

                # Add the dataframe to the table analysis object
                table_analysis.add_df(df_sampled, self.case_names[c_i])

            # Add this table analysis object to the list of tables
            self.bootstrap_tables[b_i] = table_analysis

    def set_user_defined_frequency_matrix(self, user_defined_frequency_matrix):

        # Set the user defined frequency matrix for the nominal and bootstrap tables

        # Confirm that build_bootstrap_tables() has been run
        if self.bootstrap_tables is None or self.nominal_table is None:
            raise ValueError("Tables are not built. Run build_bootstrap_tables() first.")
        
        print('Setting user defined frequency matrix for nominal and bootstrap tables')
        self.nominal_table.set_user_defined_frequency_matrix(user_defined_frequency_matrix)

        for b_i in range(self.n_bootstraps):
            self.bootstrap_tables[b_i].set_user_defined_frequency_matrix(user_defined_frequency_matrix)

        self.user_defined_frequency_matrix = user_defined_frequency_matrix


    def get_energy_in_range(self, 
        turbine_list=None, 
        wd_range=None,
        ws_range=None,
        pow_ref_range=None,
        min_points_per_bin=1,
        mean_or_median='mean',
        frequency_matrix_type='turbine',
        percentiles=[5.0, 95.0],):

        # Check that the tables is not None
        if self.bootstrap_tables is None or self.nominal_table is None:
            raise ValueError("Tables are not built. Run build_bootstrap_tables() first.")

        # Get the energy in range for the nominal table
        energy_nominal = self.nominal_table.get_energy_in_range(
            turbine_list=turbine_list,
            wd_range=wd_range,
            ws_range=ws_range,
            pow_ref_range=pow_ref_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
        )

        energy_nominal = energy_nominal[1]/ energy_nominal[0]

        # Initialize the energy as a list of zeros whose dimensions are n_bootstraps x n_cases
        energy_bootstrap = np.zeros([self.n_bootstraps])

        # Loop through the bootstraps and add the energy in range
        for b_i in range(self.n_bootstraps):
            energy_bi = self.bootstrap_tables[b_i].get_energy_in_range(
            turbine_list=turbine_list,
            wd_range=wd_range,
            ws_range=ws_range,
            pow_ref_range=pow_ref_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
            )
            energy_bootstrap[b_i] = energy_bi[1] / energy_bi[0]
        

        # Built the results array
        results_array = np.array(
                [
                energy_nominal,
                np.percentile(energy_bootstrap, percentiles[0]),
                np.percentile(energy_bootstrap, percentiles[1]),
                ]
        )
        
        # Transpose to dimensions are order cases then [nominal, lower, upper]
        # results_array = np.transpose(results_array, (1, 0))

        return results_array

    def get_energy_per_wd_bin(self, 
        turbine_list=None, 
        ws_range=None,
        pow_ref_range=None,
        min_points_per_bin=1,
        mean_or_median='mean',
        frequency_matrix_type='turbine',
        percentiles=[5.0, 95.0],):

        # Check that the tables is not None
        if self.bootstrap_tables is None or self.nominal_table is None:
            raise ValueError("Tables are not built. Run build_bootstrap_tables() first.")
        
        # Grab values for conveience
        n_wd_bins = self.nominal_table.n_wd_bins

        # Get the energy in range for the nominal table
        energy_nominal = self.nominal_table.get_energy_per_wd_bin(
            turbine_list=turbine_list,
            ws_range=ws_range,
            pow_ref_range=pow_ref_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
        )

        energy_nominal = energy_nominal[1,:]/ energy_nominal[0,:]

        # Initialize the energy as a list of zeros whose dimensions are n_bootstraps x n_cases x n_ws_bins
        energy_bootstrap = np.zeros([self.n_bootstraps, n_wd_bins])

        # Loop through the bootstraps and add the energy in range
        for b_i in range(self.n_bootstraps):
            energy_bi = self.bootstrap_tables[b_i].get_energy_per_wd_bin(
                turbine_list=turbine_list,
                ws_range=ws_range,
                pow_ref_range=pow_ref_range,
                min_points_per_bin=min_points_per_bin,
                mean_or_median=mean_or_median,
                frequency_matrix_type=frequency_matrix_type,
                )
            
            energy_bootstrap[b_i,:] = energy_bi[1,:] / energy_bi[0,:]

        # Built the results array
        results_array = np.array(
                [
                energy_nominal,
                np.percentile(energy_bootstrap, percentiles[0], axis=0),
                np.percentile(energy_bootstrap, percentiles[1], axis=0),
                ]
        ) 

        # Transpose to dimensions are order wd, [nominal, lower, upper]
        results_array = np.transpose(results_array)

        return results_array


    def get_energy_per_ws_bin(self, 
        turbine_list=None, 
        wd_range=None,
        min_points_per_bin=1,
        mean_or_median='mean',
        frequency_matrix_type='turbine',
        percentiles=[5.0, 95.0],):

        # Check that the tables is not None
        if self.bootstrap_tables is None or self.nominal_table is None:
            raise ValueError("Tables are not built. Run build_bootstrap_tables() first.")
        
        # Grab values for conveience
        n_ws_bins = self.nominal_table.n_ws_bins

        # Get the energy in range for the nominal table
        energy_nominal = self.nominal_table.get_energy_per_ws_bin(
            turbine_list=turbine_list,
            wd_range=wd_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
        )

        energy_nominal = energy_nominal[1,:]/ energy_nominal[0,:]

        # Initialize the energy as a list of zeros whose dimensions are n_bootstraps x n_cases x n_ws_bins
        energy_bootstrap = np.zeros([self.n_bootstraps, n_ws_bins])

        # Loop through the bootstraps and add the energy in range
        for b_i in range(self.n_bootstraps):
            energy_bi = self.bootstrap_tables[b_i].get_energy_per_ws_bin(
                turbine_list=turbine_list,
                wd_range=wd_range,
                min_points_per_bin=min_points_per_bin,
                mean_or_median=mean_or_median,
                frequency_matrix_type=frequency_matrix_type,
                )
            
            energy_bootstrap[b_i,:] = energy_bi[1,:] / energy_bi[0,:]

        # Built the results array
        results_array = np.array(
                [
                energy_nominal,
                np.percentile(energy_bootstrap, percentiles[0], axis=0),
                np.percentile(energy_bootstrap, percentiles[1], axis=0),
                ]
        ) 
       

        # Transpose to dimensions are order cases, ws, [nominal, lower, upper]
        results_array = np.transpose(results_array)

        return results_array
    
    def get_energy_per_pow_ref_bin(self, 
        turbine_list=None, 
        wd_range=None,
        min_points_per_bin=1,
        mean_or_median='mean',
        frequency_matrix_type='turbine',
        percentiles=[5.0, 95.0],):

        # Check that the tables is not None
        if self.bootstrap_tables is None or self.nominal_table is None:
            raise ValueError("Tables are not built. Run build_bootstrap_tables() first.")
        
        # Grab values for conveience
        n_pow_ref_bins = self.nominal_table.n_pow_ref_bins

        # Get the energy in range for the nominal table
        energy_nominal = self.nominal_table.get_energy_per_pow_ref_bin(
            turbine_list=turbine_list,
            wd_range=wd_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
        )

        energy_nominal = energy_nominal[1,:]/ energy_nominal[0,:]

        # Initialize the energy as a list of zeros whose dimensions are n_bootstraps x n_cases x n_ws_bins
        energy_bootstrap = np.zeros([self.n_bootstraps, n_pow_ref_bins])

        # Loop through the bootstraps and add the energy in range
        for b_i in range(self.n_bootstraps):
            energy_bi = self.bootstrap_tables[b_i].get_energy_per_pow_ref_bin(
                turbine_list=turbine_list,
                wd_range=wd_range,
                min_points_per_bin=min_points_per_bin,
                mean_or_median=mean_or_median,
                frequency_matrix_type=frequency_matrix_type,
                )
            
            energy_bootstrap[b_i,:] = energy_bi[1,:] / energy_bi[0,:]

        # Built the results array
        results_array = np.array(
                [
                energy_nominal,
                np.percentile(energy_bootstrap, percentiles[0], axis=0),
                np.percentile(energy_bootstrap, percentiles[1], axis=0),
                ]
        ) 
       

        # Transpose to dimensions are order cases, ws, [nominal, lower, upper]
        results_array = np.transpose(results_array)

        return results_array

    def plot_energy_per_wd_bin(self,
            turbine_list=None, 
            ws_range=None,
            pow_ref_range=None,
            min_points_per_bin=1,
            mean_or_median='mean',
            frequency_matrix_type='turbine',
            percentiles=[5.0, 95.0],
            ax=None, 
            label=None,
            **kwargs,
    ):

        # Check if label is None, and if not that they have the right length
        if label is None:
            label = f'{self.case_names[1]} / {self.case_names[0]}'

        # Get the results array
        results_array = self.get_energy_per_wd_bin(
            turbine_list=turbine_list,
            ws_range=ws_range,
            pow_ref_range=pow_ref_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
            percentiles=percentiles,
        )

        # Grab values for conveience
        wd_bin_centers = self.nominal_table.wd_bin_centers

        # If the axis is not provided, create a new one
        if ax is None:
            fig, ax = plt.subplots()

        # Loop through the cases and plot the nominal and the percentiles

        ax.plot(wd_bin_centers, 
                results_array[:, 0], 
                label=label,
                **kwargs,
        )
        ax.fill_between(wd_bin_centers, 
                        results_array[:, 1],
                            results_array[:, 2], 
                            alpha=0.3,
                            **kwargs,),
                            # color=self.case_colors[c_i],)

        # Set the labels
        ax.set_xlabel('Wind Direction [deg]')
        ax.set_ylabel('Energy Ratio [kWh]')
        ax.set_title('Energy Ratio per Wind Direction Bin')
        ax.grid(True)
        ax.legend()

        return ax
        

    def plot_energy_per_ws_bin(self,
            turbine_list=None, 
            wd_range=None,
            min_points_per_bin=1,
            mean_or_median='mean',
            frequency_matrix_type='turbine',
            percentiles=[5.0, 95.0],
            ax=None, 
            label=None,
            **kwargs,
    ):

        # Check if self.use_pow_ref is False
        if self.use_pow_ref:
            raise ValueError('Cannot plot energy per ws bin if use_pow_ref is True')

        # Check if label is None, and if not that they have the right length
        if label is None:
            label = f'{self.case_names[1]} / {self.case_names[0]}'

        # Get the results array
        results_array = self.get_energy_per_ws_bin(
            turbine_list=turbine_list,
            wd_range=wd_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
            percentiles=percentiles,
        )

        # Grab values for conveience
        ws_bin_centers = self.nominal_table.ws_bin_centers

        # If the axis is not provided, create a new one
        if ax is None:
            fig, ax = plt.subplots()

        # Loop through the cases and plot the nominal and the percentiles

        ax.plot(ws_bin_centers, 
                results_array[:, 0], 
                label=label,
                **kwargs,
        )
        ax.fill_between(ws_bin_centers, 
                        results_array[:, 1],
                            results_array[:, 2], 
                            alpha=0.3,
                            **kwargs,),
                            # color=self.case_colors[c_i],)

        # Set the labels
        ax.set_xlabel('Wind Speed [m/s]')
        ax.set_ylabel('Energy Ratio [kWh]')
        ax.set_title('Energy Ratio per Wind Speed Bin')
        ax.grid(True)
        ax.legend()

        return ax
    


    def plot_energy_per_pow_ref_bin(self,
            turbine_list=None, 
            wd_range=None,
            min_points_per_bin=1,
            mean_or_median='mean',
            frequency_matrix_type='turbine',
            percentiles=[5.0, 95.0],
            ax=None, 
            label=None,
            **kwargs,
    ):

        # Check if self.use_pow_ref is True
        if not self.use_pow_ref:
            raise ValueError('Cannot plot energy per power reference bin if use_pow_ref is False')

        # Check if label is None, and if not that they have the right length
        if label is None:
            label = f'{self.case_names[1]} / {self.case_names[0]}'

        # Get the results array
        results_array = self.get_energy_per_pow_ref_bin(
            turbine_list=turbine_list,
            wd_range=wd_range,
            min_points_per_bin=min_points_per_bin,
            mean_or_median=mean_or_median,
            frequency_matrix_type=frequency_matrix_type,
            percentiles=percentiles,
        )

        # Grab values for conveience
        pow_ref_bin_centers = self.nominal_table.pow_ref_bin_centers

        # If the axis is not provided, create a new one
        if ax is None:
            fig, ax = plt.subplots()

        # Loop through the cases and plot the nominal and the percentiles

        ax.plot(pow_ref_bin_centers, 
                results_array[:, 0], 
                label=label,
                **kwargs,
        )
        ax.fill_between(pow_ref_bin_centers, 
                        results_array[:, 1],
                            results_array[:, 2], 
                            alpha=0.3,
                            **kwargs,),
                            # color=self.case_colors[c_i],)

        # Set the labels
        ax.set_xlabel('Reference Power [kW]')
        ax.set_ylabel('Energy Ratio [kWh]')
        ax.set_title('Energy Ratio per Power Reference Bin')
        ax.grid(True)
        ax.legend()

        return ax
if __name__ == '__main__':

    tab = TableAnalysisBootstrap()

    df_baseline = pd.DataFrame({
        'ws': np.random.uniform(3, 25, 1000),
        'wd': np.random.uniform(0, 360, 1000),
        'pow_000': np.random.uniform(0, 1000, 1000),
        'pow_001': np.random.uniform(0, 1000, 1000),
        'pow_002': np.random.uniform(0, 1000, 1000)
    })

    df_control = df_baseline.copy()
    df_control['pow_000'] = df_control['pow_000'] * 1.25
    df_control['pow_000'] = np.clip(df_control['pow_000'], 0, 1000)

    tab.add_df(df_baseline, 'baseline')
    tab.add_df(df_control, 'control')

    tab.build_bootstrap_tables(n_bootstraps=20, n_blocks=10)

    print(tab.get_energy_in_range(turbine_list=[0,1]))

    print(tab.get_energy_per_ws_bin(turbine_list=[0,1]).shape)

    tab.plot_energy_per_ws_bin()


    # print(tab.get_energy_in_range_across_turbines())

    ########################################################
    # POW REF TESTS
    print('~~~~POW REF TESTS~~~~')
    df_baseline = pd.DataFrame({
        # 'ws': np.random.uniform(3, 25, 1000),
        'pow_ref': np.random.uniform(0, 1000, 1000),
        'wd': np.random.uniform(0, 360, 1000),
        'pow_000': np.random.uniform(0, 1000, 1000),
        'pow_001': np.random.uniform(0, 1000, 1000),
        'pow_002': np.random.uniform(0, 1000, 1000)
    })

    df_baseline['pow_000'] = df_baseline['pow_ref'] 

    df_control = df_baseline.copy()
    df_control['pow_000'] = df_control['pow_ref'] * 1.05
    # df_control['pow_000'] = np.clip(df_control['pow_000'], 0, 1000)

    tab = TableAnalysisBootstrap(use_pow_ref=True)
    tab.add_df(df_baseline, 'baseline')
    tab.add_df(df_control, 'control')

    tab.build_bootstrap_tables(n_bootstraps=20, n_blocks=10)

    tab.plot_energy_per_wd_bin(turbine_list=[0,1])
    tab.plot_energy_per_pow_ref_bin(turbine_list=[0,1])
    tab.plot_energy_per_ws_bin(turbine_list=[0,1])

    plt.show()
