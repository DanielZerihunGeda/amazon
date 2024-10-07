import pandas as pd
def pd_read_file(path_glob="*.pkl", ignore_index=True,  cols=None, verbose=False, nrows=-1, nfile=1000000, concat_sort=True,
                 n_pool=1, npool=None,
                 drop_duplicates=None, col_filter:str=None,  col_filter_vals:list=None, dtype_reduce=None,
                 fun_apply=None, use_ext=None,   **kw)->pd.DataFrame:
    """  Read file in parallel from disk : very Fast.
    Doc::

        path_glob: list of pattern, or sep by ";"
        :return:
    """
    import glob, gc,  pandas as pd, os

    if isinstance(path_glob, pd.DataFrame ) : return path_glob   ### Helpers

    n_pool = npool if isinstance(npool, int)  else n_pool ## alias
    def log(*s, **kw):  print(*s, flush=True, **kw)
    readers = {
            ".pkl"     : pd.read_pickle, ".parquet" : pd.read_parquet, ".json" : pd.read_json,
            ".tsv"     : pd.read_csv, ".csv"     : pd.read_csv, ".txt"     : pd.read_csv, ".zip"     : pd.read_csv,
            ".gzip"    : pd.read_csv, ".gz"      : pd.read_csv,
     }

    #### File
    if isinstance(path_glob, list):  path_glob = ";".join(path_glob)
    path_glob = path_glob.split(";")
    file_list = []
    for pi in path_glob :
        if "*" in pi : file_list.extend( sorted( glob.glob(pi) ) )
        else :         file_list.append( pi )

    file_list = sorted(list(set(file_list)))
    file_list = file_list[:nfile]
    if verbose: log(file_list)

    ### TODO : use with kewyword arguments ###############
    def fun_async(filei):
            ext  = os.path.splitext(filei)[1]
            if ext is None or ext == '': ext ='.parquet'

            pd_reader_obj = readers.get(ext, None)
            # dfi = pd_reader_obj(filei)
            try :
               dfi = pd_reader_obj(filei, **kw)
            except Exception as e:
               log('Error', filei, e)
               return pd.DataFrame()

            # if dtype_reduce is not None:    dfi = pd_dtype_reduce(dfi, int0 ='int32', float0 = 'float32')
            if col_filter is not None :       dfi = dfi[ dfi[col_filter].isin( col_filter_vals) ]
            if cols is not None :             dfi = dfi[cols]
            if nrows > 0        :             dfi = dfi.iloc[:nrows,:]
            if drop_duplicates is not None  : dfi = dfi.drop_duplicates(drop_duplicates, keep='last')
            if fun_apply is not None  :       dfi = dfi.apply(lambda  x : fun_apply(x), axis=1)
            return dfi



    ### Parallel run #################################
    import concurrent.futures
    dfall  = pd.DataFrame(columns=cols) if cols is not None else pd.DataFrame()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_pool) as executor:
        futures = []
        for i,fi in enumerate(file_list) :
            if verbose : log("file ", i, end=",")
            futures.append( executor.submit(fun_async, fi ))

        for future in concurrent.futures.as_completed(futures):
            try:
                dfi   = future.result()
                dfall = pd.concat( (dfall, dfi), ignore_index=ignore_index, sort= concat_sort)
                del dfi; gc.collect()
            except Exception as e:
                log('error', e)
    return dfall
def log(*s, **kw):
    print(*s, flush=True, **kw)
def pd_to_file(df, filei,  check=0, verbose=True, show='shape', index=False, sep="\t",   **kw):
  """function pd_to_file.
  Doc::
          
        Args:
            df:   
            filei:   
            check:   
            verbose:   
            show:   
            **kw:   
        Returns:
            
  """
  import os, gc
  from pathlib import Path
  parent = Path(filei).parent
  os.makedirs(parent, exist_ok=True)
  ext  = os.path.splitext(filei)[1]
  if   ext == ".pkl" :       df.to_pickle(filei,  **kw)
  elif ext == ".parquet" :   df.to_parquet(filei, **kw)
  elif ext in [".csv" ,".txt"] :  
    df.to_csv(filei, index=False, sep=sep, **kw)       

  elif ext in [".json" ] :  
    df.to_json(filei, **kw)       

  else :
      log('No Extension, using parquet')
      df.to_parquet(filei + ".parquet", **kw)

  if verbose in [True, 1] :  log(filei)        
  if show == 'shape':        log(df.shape)
  if show in [1, True] :     log(df)
     
  if check in [1, True, "check"] : log('Exist', os.path.isfile(filei))
  #  os_file_check( filei )

  # elif check =="checkfull" :
  #  os_file_check( filei )
  #  dfi = pd_read_file( filei, n_pool=1)   ### Full integrity
  #  log("#######  Reload Check: ",  filei, "\n"  ,  dfi.tail(3).T)
  #  del dfi; gc.collect()
  gc.collect()