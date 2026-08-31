create database emp;
use emp;
CREATE TABLE EmployeeSales (
    SaleID INT PRIMARY KEY,
    EmployeeID INT,
    Department VARCHAR(50),
    SaleAmount DECIMAL(10, 2),
    SaleDate DATE
);
INSERT INTO EmployeeSales (SaleID , EmployeeID, Department, SaleAmount, SaleDate)
VALUES 
(1, 101, 'Electronics', 500.00, '2023-08-01'),
(2, 102, 'Electronics', 300.00, '2023-08-03'),
(3, 101, 'Furniture', 150.00, '2023-08-02'),
(4, 103, 'Electronics', 250.00, '2023-08-04'),
(5, 104, 'Furniture', 200.00, '2023-08-02'),
(6, 101, 'Furniture', 450.00, '2023-08-05'),
(7, 102, 'Electronics', 700.00, '2023-08-05'),
(8, 103, 'Furniture', 100.00, '2023-08-06');

select * from EmployeeSales;
select sum(SaleAmount) as total_sale, Department from EmployeeSales group by Department;
select count(SaleID) as total_sales, EmployeeID from EmployeeSales group by EmployeeID;
select avg(SaleAmount) as avg_sale_amount, Department from EmployeeSales group by Department;
select count(SaleID) as total_sales, sum(SaleAmount) as total_sale_amount ,EmployeeID from EmployeeSales group by EmployeeID 
having total_sales > 1;
select count(SaleID) as total_sales , SaleDate from EmployeeSales group by SaleDate;