from django.db import connection
from django.conf import settings
from django.core.cache import cache

from cachebot.tests.base_tests import BaseTestCase, BasicCacheTests, FieldCacheTests, RelatedCacheTests, ExtraRelatedCacheTests
from cachebot.tests.models import FirstModel

class GetBasicCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.func = self.manager.get


class GetRelatedCacheTests(RelatedCacheTests):
    
    def setUp(self):
        RelatedCacheTests.setUp(self)
        self.func = self.manager.get


class GetExtraRelatedCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.func = self.manager.get


class GetOrCreateCacheTests(BaseTestCase):
    
    def setUp(self):
        BaseTestCase.setUp(self)
    
    def test_get_then_create(self):
        self.assertRaises(FirstModel.DoesNotExist, FirstModel.objects.get, **{'text':'new'})
        FirstModel.objects.create(text='new')
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,False)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,True)
    
    def test_get_or_create(self):
        obj, created = FirstModel.objects.get_or_create(text='new')
        self.assertEqual(created, True)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,False)
        obj = FirstModel.objects.get(text='new')
        self.assertEqual(obj.from_cache,True)

class SelectRelatedCacheTests(ExtraRelatedCacheTests):

    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.func = self.manager.select_related().cache().filter
        self.obj = self.thirdmodel
        self.kwargs = {'id':self.obj.id}

class ExcludeCacheTests(BasicCacheTests):
    
    def setUp(self):
        BasicCacheTests.setUp(self)
        self.obj = self.thirdmodel
        self.kwargs = {'id':self.obj.id+1}
        self.func = self.manager.cache().exclude


class ExcludeFieldCacheTests(FieldCacheTests):
    
    def setUp(self):
        FieldCacheTests.setUp(self)
        self.kwargs = {'text':'this text is not in any model'}
        self.func = self.manager.cache().exclude
        

class ExtraRelatedExcludeCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj':self.obj.obj.obj.id+1}
        self.func = self.manager.cache().exclude


class RangeCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        self.kwargs = {'obj__obj__in':[self.firstmodel]}
        
        
class NestedQuerysetCacheTests(ExtraRelatedCacheTests):
    
    def setUp(self):
        ExtraRelatedCacheTests.setUp(self)
        queryset = FirstModel.objects.all()
        self.kwargs = {'obj__obj__in':queryset}
        
        
class CountCacheTests(BasicCacheTests):
    
    def setUp(self):
        settings.DEBUG = True
        BasicCacheTests.setUp(self)
    
    def test_lookup(self, count=1):
        cache.clear()
        # call count to create any CacheBotSignals first
        self.assertEqual(self.func(**self.kwargs).count(), count)
        
        connection.queries = []
        cache.clear()
        self.assertEqual(self.func(**self.kwargs).count(), count)
        self.assertEqual(len(connection.queries), 1)
        cache.clear()
        self.assertEqual(self.func(**self.kwargs).count(), count)
        self.assertEqual(len(connection.queries), 2)
    
    def test_save_signal(self, obj=None):
        if obj is None:
            obj = self.obj
        self.test_lookup(count=1)
        obj.save()
        self.test_lookup(count=1)
    
    def test_delete_signal(self, obj=None):
        if obj is None:
            obj = self.obj
        self.test_lookup(count=1)
        obj.delete()
        self.test_lookup(count=0)
    
    def test_related_save_signal(self):
        self.test_save_signal(obj=self.obj.obj)
    
    def test_related_delete_signal(self):
        self.test_delete_signal(obj=self.obj.obj)
    
    def test_extra_related_save_signal(self):
        self.test_save_signal(obj=self.obj.obj.obj)
    
    def test_extra_related_delete_signal(self):
        self.test_delete_signal(obj=self.obj.obj.obj)
        
    