#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Andy Sayler
# Summer 2014
# Univerity of Colorado

import copy
import random
import time
import unittest
import uuid

import redis

import test_common
import backend_redis as backend


class BackendRedisTestCase(test_common.CogsTestCase):

    def setUp(self):
        super(BackendRedisTestCase, self).setUp()

    def tearDown(self):
        super(BackendRedisTestCase, self).tearDown()


class RedisObjectTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisObjectTestCase, self).setUp()

        self.key = 'key'
        self.rid = "object+{:s}".format(self.key)
        self.val = 'val'

        self.db.set(self.rid, self.val)

        self.ObjFactory = backend.Factory(backend.ObjectBase, db=self.db)

    def tearDown(self):
        super(RedisObjectTestCase, self).tearDown()

    def test_from_new(self):

        # Test w/o Key
        self.assertRaises(backend.ObjectError, self.ObjFactory.from_new)

        # Test w/ Key
        self.assertTrue(self.ObjFactory.from_new('newkey'))

        # Test w/ Duplicate Key
        self.assertRaises(backend.ObjectError, self.ObjFactory.from_new, self.key)

        # Test w/ Illegal Key ':'
        self.assertRaises(backend.ObjectError, self.ObjFactory.from_new, 'test:1')

        # Test w/ Illegal Key '_'
        self.assertRaises(backend.ObjectError, self.ObjFactory.from_new, 'test+1')

    def test_from_existing(self):

        # Test Non-Existant Object
        self.assertRaises(backend.ObjectDNE, self.ObjFactory.from_existing, 'badkey')

        # Test Existing Object
        self.assertTrue(self.ObjFactory.from_existing(self.key))

    def test_from_raw(self):

        # Test Non-Existant Object
        self.assertTrue(self.ObjFactory.from_existing(self.key))

        # Test Existing Object
        self.assertTrue(self.ObjFactory.from_existing(self.key))

    def test_str(self):

        # Test Not Equal
        s1 = str(self.ObjFactory.from_new('str1'))
        s2 = str(self.ObjFactory.from_new('str2'))
        self.assertFalse(s1 == s2)

        # Test Equal
        s1 = str(self.ObjFactory.from_new('str1'))
        s2 = str(self.ObjFactory.from_new('str1'))
        self.assertTrue(s1 == s2)

    def test_hash(self):

        # Test Not Equal
        h1 = hash(self.ObjFactory.from_new('hash1'))
        h2 = hash(self.ObjFactory.from_new('hash2'))
        self.assertFalse(h1 == h2)

        # Test Equal
        h1 = hash(self.ObjFactory.from_new('hash1'))
        h2 = hash(self.ObjFactory.from_new('hash1'))
        self.assertTrue(h1 == h2)

    def test_eq(self):

        # Test Not Equal
        o1 = self.ObjFactory.from_new('eq1')
        o2 = self.ObjFactory.from_new('eq2')
        self.assertFalse(o1 == o2)

        # Test Equal
        o1 = self.ObjFactory.from_new('eq1')
        o2 = self.ObjFactory.from_new('eq1')
        self.assertTrue(o1 == o2)

    def test_delete(self):

        # Test Delete
        o = self.ObjFactory.from_existing(self.key)
        self.assertTrue(self.db.exists(self.rid))
        o.delete()
        self.assertFalse(self.db.exists(self.rid))


class RedisFactoryTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisFactoryTestCase, self).setUp()

    def tearDown(self):
        super(RedisFactoryTestCase, self).tearDown()

    def test_init(self):

        # Test w/o Prefix or Key
        of = backend.Factory(backend.ObjectBase, db=self.db)
        self.assertRaises(backend.ObjectError, of.from_new)

        # Test w/ Prefix but w/o Key
        p = "testprefix_{:03d}".format(random.randint(0, 999))
        of = backend.Factory(backend.ObjectBase, prefix=p, db=self.db)
        o = of.from_new()
        self.assertTrue(o)

        # Test w/ Key but w/o Prefix
        k = "testkey_{:03d}".format(random.randint(0, 999))
        of = backend.Factory(backend.ObjectBase, db=self.db)
        o = of.from_new(k)
        self.assertTrue(o)

        # Test w/ Prefix and Key
        p = "testprefix_{:03d}".format(random.randint(0, 999))
        k = "testkey_{:03d}".format(random.randint(0, 999))
        of = backend.Factory(backend.ObjectBase, prefix=p, db=self.db)
        o = of.from_new(k)
        self.assertTrue(o)

    def test_list(self):

        val = 'val'
        pre = 'test'

        # Add Parents w/o Prefix
        self.db.flushdb()
        parents = ['p01', 'p02', 'p03']
        for p in parents:
            self.db.set("object+{:s}".format(p), val)

        # Test Parents w/o Prefix
        hf = backend.Factory(backend.ObjectBase, db=self.db)
        fam = hf.list_family()
        self.assertEqual(set(parents), fam)
        sib = hf.list_siblings()
        self.assertEqual(set(parents), sib)
        chd = hf.list_children()
        self.assertFalse(chd)

        # Add Parents w/ Prefix
        self.db.flushdb()
        parents = ['p01', 'p02', 'p03']
        for p in parents:
            self.db.set("{:s}:object+{:s}".format(pre, p), val)

        # Test Parents w/ Prefix
        hf = backend.Factory(backend.ObjectBase, prefix=pre, db=self.db)
        fam = hf.list_family()
        self.assertEqual(set(parents), fam)
        sib = hf.list_siblings()
        self.assertEqual(set(parents), sib)
        chd = hf.list_children()
        self.assertEqual(set([]), chd)

        # Add Parents + Children w/o Prefix
        self.db.flushdb()
        parents = ['p01', 'p02', 'p03']
        for p in parents:
            self.db.set("object+{:s}".format(p), val)
        p1_children = ['c01', 'c02', 'c03']
        full_children = []
        for c in p1_children:
            child = "{:s}:object+{:s}".format(parents[0], c)
            self.db.set("object+{:s}".format(child), val)
            full_children.append(child)

        # Test Parents + Children w/o Prefix
        hf = backend.Factory(backend.ObjectBase, db=self.db)
        fam = hf.list_family()
        self.assertEqual(set(parents + full_children), fam)
        sib = hf.list_siblings()
        self.assertEqual(set(parents), sib)
        chd = hf.list_children()
        self.assertEqual(set(full_children), chd)

        # Test Children w/o Prefix
        chd_pre = "object+{:s}".format(parents[0])
        hf = backend.Factory(backend.ObjectBase, prefix=chd_pre, db=self.db)
        fam = hf.list_family()
        self.assertEqual(set(p1_children), fam)
        sib = hf.list_siblings()
        self.assertEqual(set(p1_children), sib)
        chd = hf.list_children()
        self.assertEqual(set([]), chd)

        # Add Parents + Children w/ Prefix
        self.db.flushdb()
        parents = ['p01', 'p02', 'p03']
        for p in parents:
            self.db.set("{:s}:object+{:s}".format(pre, p), val)
        p1_children = ['c01', 'c02', 'c03']
        full_children = []
        for c in p1_children:
            child = "{:s}:object+{:s}".format(parents[0], c)
            self.db.set("{:s}:object+{:s}".format(pre, child), val)
            full_children.append(child)

        # Test Parents + Children w/ Prefix
        hf = backend.Factory(backend.ObjectBase, prefix=pre, db=self.db)
        fam = hf.list_family()
        self.assertEqual(set(parents + full_children), fam)
        sib = hf.list_siblings()
        self.assertEqual(set(parents), sib)
        chd = hf.list_children()
        self.assertEqual(set(full_children), chd)

        # Test Children w/ Prefix
        chd_pre = "{:s}:object+{:s}".format(pre, parents[0])
        hf = backend.Factory(backend.ObjectBase, prefix=chd_pre, db=self.db)
        fam = hf.list_family()
        self.assertEqual(set(p1_children), fam)
        sib = hf.list_siblings()
        self.assertEqual(set(p1_children), sib)
        chd = hf.list_children()
        self.assertEqual(set([]), chd)

    def test_get(self):

        val = 'val'

        # Add Parents w/o Prefix
        self.db.flushdb()
        parents = ['p01', 'p02', 'p03']
        for p in parents:
            self.db.set("object+{:s}".format(p), val)

        # Test Parents w/o Prefix
        hf = backend.Factory(backend.ObjectBase, db=self.db)
        sibs = hf.get_siblings()
        self.assertEqual(set(parents), set([s.key() for s in sibs]))


class RedisUUIDFactoryTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisUUIDFactoryTestCase, self).setUp()

    def tearDown(self):
        super(RedisUUIDFactoryTestCase, self).tearDown()

    def test_init(self):

        # Test w/o Prefix
        of = backend.UUIDFactory(backend.ObjectBase, db=self.db)
        o = of.from_new()
        self.assertTrue(o)

        # Test w/ Prefix
        p = "testprefix_{:03d}".format(random.randint(0, 999))
        of = backend.UUIDFactory(backend.ObjectBase, prefix=p, db=self.db)
        o = of.from_new()
        self.assertTrue(o)


class RedisHashTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisHashTestCase, self).setUp()

        self.HashFactory = backend.Factory(backend.HashBase, db=self.db)

    def tearDown(self):
        super(RedisHashTestCase, self).tearDown()

    def test_from_new(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Test Empty Dict w/o Key
        d = {}
        self.assertRaises(backend.ObjectError, self.HashFactory.from_new, d)

        # Test Empty Dict w/ Key
        d = {}
        self.assertRaises(backend.ObjectError, self.HashFactory.from_new, d, k)

        # Test Non-Empty Dict w/o Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        self.assertRaises(backend.ObjectError, self.HashFactory.from_new, d)

        # Test Non-Empty Dict w Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h = self.HashFactory.from_new(d, k)
        self.assertSubset(d, h.get_dict())

    def test_from_existing(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Test Non-Existant Object
        self.assertRaises(backend.ObjectDNE, self.HashFactory.from_existing, k)

        # Test Existing Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h1 = self.HashFactory.from_new(d, k)
        self.assertSubset(d, h1.get_dict())
        h2 = self.HashFactory.from_existing(k)
        self.assertEqual(h1, h2)
        self.assertEqual(h1.get_dict(), h2.get_dict())

    def test_from_raw(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Test Non-Existant Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h1 = self.HashFactory.from_raw(k)
        self.assertFalse(h1.get_dict())
        h1.set_dict(d)
        self.assertSubset(d, h1.get_dict())

        # Test Existing Object
        h2 = self.HashFactory.from_raw(k)
        self.assertSubset(d, h2.get_dict())

        # Compare Objects
        self.assertEqual(h1, h2)
        self.assertEqual(h1.get_dict(), h2.get_dict())

    def test_get_dict(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create and Get Object
        d_in = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d_in, k)
        d_out = obj.get_dict()
        self.assertSubset(d_in, d_out)

    def test_set_dict(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create and Get Object
        d1_in = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d1_in, k)
        d1_out = obj.get_dict()
        self.assertSubset(d1_in, d1_out)

        # Update and Get Object
        d2_in = copy.deepcopy(test_common.DUMMY_TESTDICT)
        for k in d2_in:
            d2_in[k] = "set_dict_test_val_{:s}".format(k)
        self.assertNotEqual(d1_in, d2_in)
        obj.set_dict(d2_in)
        d2_out = obj.get_dict()
        self.assertSubset(d2_in, d2_out)

    def test_getitem(self):

        # Temp Get Funcation
        def get_item(d, key):
            return d[key]

        # Create Object Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d, k)

        # Test Bad Key
        self.assertFalse(obj['test'])

        # Test Good Keys
        for key in d:
            self.assertEqual(d[key], obj[key])

    def test_setitem(self):

        # Temp Set Function
        def set_item(d, key, val):
            d[key] = val

        # Create Object Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        obj = self.HashFactory.from_new(d, k)

        # Test Keys
        for key in d:
            val = d[key] + "_updated"
            obj[key] = val
            self.assertEqual(val, obj[key])


class RedisTSHashTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisTSHashTestCase, self).setUp()

        self.TSHashFactory = backend.Factory(backend.TSHashBase, db=self.db)

    def tearDown(self):
        super(RedisTSHashTestCase, self).tearDown()

    def test_from_new(self):

        # Test Empty Dict w/o Key
        d = {}
        self.assertRaises(backend.ObjectError, self.TSHashFactory.from_new, d)

        # Test Empty Dict w/ Key
        d = {}
        k = "testkey_1"
        h = self.TSHashFactory.from_new(d, key=k)
        self.assertSubset(d, h.get_dict())
        self.assertEqual(h['created_time'], h['modified_time'])

        # Test Non-Empty Dict w/o Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        self.assertRaises(backend.ObjectError, self.TSHashFactory.from_new, d)

        # Test Non-Empty Dict w Key
        k = "testkey_2"
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h = self.TSHashFactory.from_new(d, key=k)
        self.assertSubset(d, h.get_dict())
        self.assertEqual(h['created_time'], h['modified_time'])

    def test_set_dict(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create and Get Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h = self.TSHashFactory.from_new(d, key=k)
        self.assertSubset(d, h.get_dict())
        ct0 = float(h['created_time'])
        mt0 = float(h['modified_time'])
        self.assertEqual(ct0, mt0)

        # Update and Get Object
        time.sleep(0.01)
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        for k in d:
            d[k] = "set_dict_test_val_{:s}".format(k)
        self.assertNotEqual(d, test_common.DUMMY_TESTDICT)
        h.set_dict(d)
        self.assertSubset(d, h.get_dict())
        ct1 = float(h['created_time'])
        mt1 = float(h['modified_time'])
        self.assertEqual(ct0, ct1)
        self.assertTrue(ct1 < mt1)
        self.assertTrue(mt0 < mt1)

    def test_setitem(self):

        # Temp Set Function
        def set_item(d, key, val):
            d[key] = val

        # Create Object Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h = self.TSHashFactory.from_new(d, key=k)
        self.assertSubset(d, h.get_dict())
        ct0 = float(h['created_time'])
        mt0 = float(h['modified_time'])
        self.assertEqual(ct0, mt0)

        # Test Keys
        for key in d:
            time.sleep(0.01)
            val = d[key] + "_updated"
            h[key] = val
            self.assertEqual(val, h[key])
            ct1 = float(h['created_time'])
            mt1 = float(h['modified_time'])
            self.assertEqual(ct0, ct1)
            self.assertTrue(ct1 < mt1)
            self.assertTrue(mt0 < mt1)
            mt0 = mt1


class RedisUUIDHashTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisUUIDHashTestCase, self).setUp()

        self.UUIDHashFactory = backend.UUIDFactory(backend.HashBase, db=self.db)

    def tearDown(self):
        super(RedisUUIDHashTestCase, self).tearDown()

    def test_from_new(self):

        # Test Empty Dict
        d = {}
        self.assertRaises(backend.ObjectError, self.UUIDHashFactory.from_new, d)

        # Test Non-Empty Dict w/o Key
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h = self.UUIDHashFactory.from_new(d)
        self.assertSubset(d, h.get_dict())

    def test_from_existing(self):

        k = uuid.UUID("01c47915-4777-11d8-bc70-0090272ff725")

        # Test Non-Existant Object
        self.assertRaises(backend.ObjectDNE, self.UUIDHashFactory.from_existing, k)

        # Test Existing Object
        d = copy.deepcopy(test_common.DUMMY_TESTDICT)
        h1 = self.UUIDHashFactory.from_new(d)
        self.assertSubset(d, h1.get_dict())
        h2 = self.UUIDHashFactory.from_existing(h1.key())
        self.assertEqual(h1, h2)
        self.assertEqual(h1.get_dict(), h2.get_dict())


class RedisSetTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisSetTestCase, self).setUp()

        self.SetFactory = backend.Factory(backend.SetBase, db=self.db)

    def tearDown(self):
        super(RedisSetTestCase, self).tearDown()

    def test_from_new(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Test Empty Set w/o Key
        v = set([])
        self.assertRaises(backend.ObjectError, self.SetFactory.from_new, v)

        # Test Empty Dict w/ Key
        v = set([])
        self.assertRaises(backend.ObjectError, self.SetFactory.from_new, v, k)

        # Test Non-Empty Dict w/o Key
        v = set(['a', 'b', 'c'])
        self.assertRaises(backend.ObjectError, self.SetFactory.from_new, v)

        # Test Non-Empty Dict w/ Key
        v = set(['a', 'b', 'c'])
        s = self.SetFactory.from_new(v, k)
        self.assertEqual(v, s.get_set())

    def test_from_existing(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Test Non-Existant Object
        self.assertRaises(backend.ObjectDNE, self.SetFactory.from_existing, k)

        # Test Existing Object
        v = set(['a', 'b', 'c'])
        s1 = self.SetFactory.from_new(v, k)
        self.assertEqual(v, s1.get_set())
        s2 = self.SetFactory.from_existing(k)
        self.assertEqual(s1, s2)
        self.assertEqual(s1.get_set(), s2.get_set())

    def test_from_raw(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Test Non-Existant Object
        v = set(['a', 'b', 'c'])
        s1 = self.SetFactory.from_raw(k)
        self.assertFalse(s1.get_set())
        s1.add_vals(v)
        self.assertEqual(v, s1.get_set())

        # Test Existing Object
        s2 = self.SetFactory.from_raw(k)
        self.assertEqual(v, s2.get_set())

        # Compare Objects
        self.assertEqual(s1, s2)
        self.assertEqual(s1.get_set(), s2.get_set())

    def test_get_set(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create and get set
        v = set(['a', 'b', 'c'])
        s = self.SetFactory.from_new(v, k)
        self.assertEqual(v, s.get_set())

    def test_add_vals(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create and get set
        v1 = set(['a', 'b', 'c'])
        s = self.SetFactory.from_new(v1, k)
        self.assertEqual(v1, s.get_set())

        # Add New Vals
        v2 = set(['d', 'e'])
        s.add_vals(v2)
        self.assertEqual((v1 | v2), s.get_set())

        # Add Existing Vals
        v3 = set(['d', 'e'])
        s.add_vals(v3)
        self.assertEqual((v1 | v2 | v3), s.get_set())

    def test_del_vals(self):

        # Create Key
        k = "testkey_{:03d}".format(random.randint(0, 999))

        # Create and get set
        v1 = set(['a', 'b', 'c', 'd', 'e'])
        s = self.SetFactory.from_new(v1, k)
        self.assertEqual(v1, s.get_set())

        # Remove Existing Vals
        v2 = set(['d', 'e'])
        self.assertEqual(s.del_vals(v2), len(v2))
        self.assertEqual((v1 - v2), s.get_set())

        # Remove Existing Vals
        v3 = set(['d', 'e'])
        self.assertEqual(s.del_vals(v3), 0)
        self.assertEqual((v1 - v2 - v3), s.get_set())


class RedisUUIDSetTestCase(BackendRedisTestCase):

    def setUp(self):
        super(RedisUUIDSetTestCase, self).setUp()

        self.UUIDSetFactory = backend.UUIDFactory(backend.SetBase, db=self.db)

    def tearDown(self):
        super(RedisUUIDSetTestCase, self).tearDown()

    def test_from_new(self):

        # Test Empty Set
        v = set([])
        self.assertRaises(backend.ObjectError, self.UUIDSetFactory.from_new, v)

        # Test Non-Empty Dict w/o Key
        v = set(['a', 'b', 'c'])
        s = self.UUIDSetFactory.from_new(v)
        self.assertSubset(v, s.get_set())

    def test_from_existing(self):

        k = uuid.UUID("01c47915-4777-11d8-bc70-0090272ff725")

        # Test Non-Existant Object
        self.assertRaises(backend.ObjectDNE, self.UUIDSetFactory.from_existing, k)

        # Test Existing Object
        v = set(['a', 'b', 'c'])
        s1 = self.UUIDSetFactory.from_new(v)
        self.assertSubset(v, s1.get_set())
        s2 = self.UUIDSetFactory.from_existing(s1.key())
        self.assertEqual(s1, s2)
        self.assertEqual(s1.get_set(), s2.get_set())


### Main ###
if __name__ == '__main__':
    unittest.main()
