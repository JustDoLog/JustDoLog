from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from blog.management.commands.generate_test_data import Command
from blog.models import Post
from user.models import CustomUser
import random


class GenerateTestDataTests(TestCase):
    def setUp(self):
        self.command = Command(test_mode=True)
        self.now = timezone.now()
        
        # 테스트용 사용자 생성
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_generate_distributed_dates(self):
        """날짜 분포 테스트"""
        dates = [self.command.generate_distributed_dates() for _ in range(1000)]
        
        # 날짜별 분포 계산
        daily = sum(1 for d in dates if (self.now - d).days < 1)
        weekly = sum(1 for d in dates if 1 <= (self.now - d).days < 7)
        monthly = sum(1 for d in dates if 7 <= (self.now - d).days < 30)
        yearly = sum(1 for d in dates if (self.now - d).days >= 30)
        
        # 분포 비율 계산
        total = len(dates)
        daily_ratio = daily / total
        weekly_ratio = weekly / total
        monthly_ratio = monthly / total
        yearly_ratio = yearly / total
        
        # 각 기간별 예상 비율과 허용 오차
        expected_distributions = [
            (daily_ratio, 0.30, 0.1),    # 일간: 30% ± 10%
            (weekly_ratio, 0.30, 0.1),   # 주간: 30% ± 10%
            (monthly_ratio, 0.25, 0.1),  # 월간: 25% ± 10%
            (yearly_ratio, 0.15, 0.1),   # 연간: 15% ± 10%
        ]
        
        # 각 분포 검증
        for actual, expected, delta in expected_distributions:
            self.assertAlmostEqual(
                actual, 
                expected, 
                delta=delta,
                msg=f"Distribution test failed: expected {expected:.2%} ± {delta:.2%}, got {actual:.2%}"
            )
            
        # 전체 합이 1인지 확인
        total_ratio = daily_ratio + weekly_ratio + monthly_ratio + yearly_ratio
        self.assertAlmostEqual(
            total_ratio, 
            1.0, 
            delta=0.01,
            msg=f"Total distribution should be 100%, got {total_ratio:.2%}"
        )

    def test_metrics_ranges(self):
        """각 기간별 메트릭 범위 테스트"""
        test_cases = [
            (timedelta(hours=12), (1, 49)),    # 일간
            (timedelta(days=3), (50, 99)),     # 주간
            (timedelta(days=15), (100, 299)),  # 월간
            (timedelta(days=100), (300, 999))  # 연간
        ]
        
        for delta, (min_val, max_val) in test_cases:
            date = self.now - delta
            metrics = self.command.calculate_engagement_metrics(date)
            
            self.assertTrue(
                min_val <= metrics['views'] <= max_val,
                f"Views for {delta} should be between {min_val} and {max_val}, got {metrics['views']}"
            )
            self.assertTrue(
                min_val <= metrics['likes'] <= max_val,
                f"Likes for {delta} should be between {min_val} and {max_val}, got {metrics['likes']}"
            )

    def test_strict_period_boundaries(self):
        """기간 경계값 테스트"""
        # 각 기간의 경계값 테스트
        boundaries = [
            (timedelta(hours=23), (1, 49)),     # 일간 경계
            (timedelta(days=6), (50, 99)),      # 주간 경계
            (timedelta(days=29), (100, 299)),   # 월간 경계
            (timedelta(days=31), (300, 999))    # 연간 시작
        ]
        
        for delta, (min_val, max_val) in boundaries:
            date = self.now - delta
            metrics = self.command.calculate_engagement_metrics(date)
            
            self.assertTrue(
                min_val <= metrics['views'] <= max_val,
                f"Boundary test failed for {delta}: views={metrics['views']}"
            )
            self.assertTrue(
                min_val <= metrics['likes'] <= max_val,
                f"Boundary test failed for {delta}: likes={metrics['likes']}"
            )

    def test_no_overlap_between_periods(self):
        """기간별 메트릭이 겹치지 않는지 테스트"""
        test_dates = [
            self.now - timedelta(hours=1),   # 일간
            self.now - timedelta(days=3),    # 주간
            self.now - timedelta(days=15),   # 월간
            self.now - timedelta(days=100)   # 연간
        ]
        
        metrics_list = [
            self.command.calculate_engagement_metrics(date)
            for date in test_dates
        ]
        
        # 각 기간의 최대값이 다음 기간의 최소값보다 작은지 확인
        for i in range(len(metrics_list) - 1):
            current_metrics = metrics_list[i]
            next_metrics = metrics_list[i + 1]
            
            self.assertLess(
                max(current_metrics['views'], current_metrics['likes']),
                min(next_metrics['views'], next_metrics['likes']),
                f"Overlap detected between periods {i} and {i+1}"
            ) 