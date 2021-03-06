"""Test kipoi.writers
"""
from pytest import fixture
from kipoi.metadata import GenomicRanges
from kipoi.writers import BedBatchWriter, TsvBatchWriter, HDF5BatchWriter
from kipoi.readers import HDF5Reader
from kipoi.cli.main import prepare_batch
import numpy as np
import pandas as pd
from kipoi.components import DataLoaderSchema, ArraySchema, MetadataStruct, MetadataType
from collections import OrderedDict


@fixture
def metadata_schema():
    return OrderedDict([("ranges", MetadataStruct(type=MetadataType.GENOMIC_RANGES, doc="ranges")),
                        ("gene_id", MetadataStruct(type=MetadataType.STR, doc="gene id"))])


@fixture
def dl_batch():
    return {"inputs": np.arange(3),
            "metadata": {
        "ranges": GenomicRanges(chr=np.array(["chr1", "chr1", "chr1"]),
                                start=np.arange(3) + 1,
                                end=np.arange(3) + 5,
                                id=np.arange(3).astype(str),
                                strand=np.array(["*"] * 3)
                                ),
        "gene_id": np.arange(3).astype(str)
    }}


@fixture
def pred_batch_array():
    return np.arange(9).reshape((3, 3))


@fixture
def pred_batch_list():
    return [np.arange(9).reshape((3, 3)),
            np.arange(9).reshape((3, 3))]


@fixture
def pred_batch_dict():
    return {"first": np.arange(9).reshape((3, 3)),
            "second": np.arange(9).reshape((3, 3))}


# pred_batch_array = pred_batch_array()
# dl_batch = dl_batch()
# tmpfile = "/tmp/kipoi/test.tsv"
# metadata_schema = metadata_schema()
# --------------------------------------------


def test_TsvBatchWriter_array(dl_batch, pred_batch_array, tmpdir):
    tmpfile = str(tmpdir.mkdir("example").join("out.tsv"))
    writer = TsvBatchWriter(tmpfile)
    batch = prepare_batch(dl_batch, pred_batch_array)
    writer.batch_write(batch)
    writer.batch_write(batch)
    writer.close()
    df = pd.read_csv(tmpfile, sep="\t")

    assert set(list(df.columns)) == {'metadata/ranges/id',
                                     'metadata/ranges/strand',
                                     'metadata/ranges/chr',
                                     'metadata/ranges/start',
                                     'metadata/ranges/end',
                                     'metadata/gene_id',
                                     'preds/0',
                                     'preds/1',
                                     'preds/2'}
    assert list(df['metadata/ranges/id']) == [0, 1, 2, 0, 1, 2]


def test_HDF5BatchWriter_array(dl_batch, pred_batch_array, tmpdir):
    tmpfile = str(tmpdir.mkdir("example").join("out.h5"))
    batch = prepare_batch(dl_batch, pred_batch_array)
    writer = HDF5BatchWriter(tmpfile, chunk_size=4)

    writer.batch_write(batch)
    writer.batch_write(batch)
    writer.close()
    with HDF5Reader(tmpfile) as f:
        assert np.all(list(f.batch_iter(2))[0]['metadata']['gene_id'] == dl_batch['metadata']['gene_id'][:2])
        out = f.load_all()
        assert np.all(out['metadata']['gene_id'] == np.concatenate([dl_batch['metadata']['gene_id'], dl_batch['metadata']['gene_id']]))
        assert np.all(out['metadata']['ranges']["chr"] == np.concatenate([dl_batch['metadata']['ranges']['chr'],
                                                                          dl_batch['metadata']['ranges']['chr']]))
        assert np.all(out['metadata']['ranges']["start"] == np.concatenate([dl_batch['metadata']['ranges']['start'],
                                                                            dl_batch['metadata']['ranges']['start']]))
        assert np.all(out['preds'][:3] == pred_batch_array)


def test_HDF5BatchWriter_list(dl_batch, pred_batch_list, tmpdir):
    tmpfile = str(tmpdir.mkdir("example").join("out.h5"))
    batch = prepare_batch(dl_batch, pred_batch_list)
    writer = HDF5BatchWriter(tmpfile, chunk_size=4)

    writer.batch_write(batch)
    writer.batch_write(batch)
    writer.close()
    with HDF5Reader(tmpfile) as f:
        assert np.all(list(f.batch_iter(2))[0]['metadata']['gene_id'] == dl_batch['metadata']['gene_id'][:2])
        out = f.load_all()
        assert np.all(out['metadata']['gene_id'] == np.concatenate([dl_batch['metadata']['gene_id'], dl_batch['metadata']['gene_id']]))
        assert np.all(out['metadata']['ranges']["chr"] == np.concatenate([dl_batch['metadata']['ranges']['chr'],
                                                                          dl_batch['metadata']['ranges']['chr']]))
        assert np.all(out['metadata']['ranges']["start"] == np.concatenate([dl_batch['metadata']['ranges']['start'],
                                                                            dl_batch['metadata']['ranges']['start']]))
        assert np.all(out['preds'][0][:3] == pred_batch_list[0])


def test_BedBatchWriter(dl_batch, pred_batch_array, metadata_schema, tmpdir):
    tmpfile = str(tmpdir.mkdir("example").join("out.tsv"))
    writer = BedBatchWriter(tmpfile, metadata_schema=metadata_schema)
    batch = prepare_batch(dl_batch, pred_batch_array)
    writer.batch_write(batch)
    writer.batch_write(batch)
    writer.close()
    df = pd.read_csv(tmpfile, sep="\t")

    assert list(df.columns) == ['chr',
                                'start',
                                'end',
                                'name',
                                'score',
                                'strand',
                                'preds/0',
                                'preds/1',
                                'preds/2']
    assert list(df['name']) == [0, 1, 2, 0, 1, 2]
