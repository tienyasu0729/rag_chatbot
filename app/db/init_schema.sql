USE [master]
GO
/****** Object:  Database [usedCars]    Script Date: 03/05/2026 12:09:59 CH ******/
CREATE DATABASE [usedCars]
 CONTAINMENT = NONE
 ON  PRIMARY 
( NAME = N'usedCars', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\usedCars.mdf' , SIZE = 73728KB , MAXSIZE = UNLIMITED, FILEGROWTH = 65536KB )
 LOG ON 
( NAME = N'usedCars_log', FILENAME = N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\usedCars_log.ldf' , SIZE = 73728KB , MAXSIZE = 2048GB , FILEGROWTH = 65536KB )
 WITH CATALOG_COLLATION = DATABASE_DEFAULT
GO
ALTER DATABASE [usedCars] SET COMPATIBILITY_LEVEL = 150
GO
IF (1 = FULLTEXTSERVICEPROPERTY('IsFullTextInstalled'))
begin
EXEC [usedCars].[dbo].[sp_fulltext_database] @action = 'enable'
end
GO
ALTER DATABASE [usedCars] SET ANSI_NULL_DEFAULT OFF 
GO
ALTER DATABASE [usedCars] SET ANSI_NULLS OFF 
GO
ALTER DATABASE [usedCars] SET ANSI_PADDING OFF 
GO
ALTER DATABASE [usedCars] SET ANSI_WARNINGS OFF 
GO
ALTER DATABASE [usedCars] SET ARITHABORT OFF 
GO
ALTER DATABASE [usedCars] SET AUTO_CLOSE OFF 
GO
ALTER DATABASE [usedCars] SET AUTO_SHRINK OFF 
GO
ALTER DATABASE [usedCars] SET AUTO_UPDATE_STATISTICS ON 
GO
ALTER DATABASE [usedCars] SET CURSOR_CLOSE_ON_COMMIT OFF 
GO
ALTER DATABASE [usedCars] SET CURSOR_DEFAULT  GLOBAL 
GO
ALTER DATABASE [usedCars] SET CONCAT_NULL_YIELDS_NULL OFF 
GO
ALTER DATABASE [usedCars] SET NUMERIC_ROUNDABORT OFF 
GO
ALTER DATABASE [usedCars] SET QUOTED_IDENTIFIER OFF 
GO
ALTER DATABASE [usedCars] SET RECURSIVE_TRIGGERS OFF 
GO
ALTER DATABASE [usedCars] SET  ENABLE_BROKER 
GO
ALTER DATABASE [usedCars] SET AUTO_UPDATE_STATISTICS_ASYNC OFF 
GO
ALTER DATABASE [usedCars] SET DATE_CORRELATION_OPTIMIZATION OFF 
GO
ALTER DATABASE [usedCars] SET TRUSTWORTHY OFF 
GO
ALTER DATABASE [usedCars] SET ALLOW_SNAPSHOT_ISOLATION OFF 
GO
ALTER DATABASE [usedCars] SET PARAMETERIZATION SIMPLE 
GO
ALTER DATABASE [usedCars] SET READ_COMMITTED_SNAPSHOT OFF 
GO
ALTER DATABASE [usedCars] SET HONOR_BROKER_PRIORITY OFF 
GO
ALTER DATABASE [usedCars] SET RECOVERY FULL 
GO
ALTER DATABASE [usedCars] SET  MULTI_USER 
GO
ALTER DATABASE [usedCars] SET PAGE_VERIFY CHECKSUM  
GO
ALTER DATABASE [usedCars] SET DB_CHAINING OFF 
GO
ALTER DATABASE [usedCars] SET FILESTREAM( NON_TRANSACTED_ACCESS = OFF ) 
GO
ALTER DATABASE [usedCars] SET TARGET_RECOVERY_TIME = 60 SECONDS 
GO
ALTER DATABASE [usedCars] SET DELAYED_DURABILITY = DISABLED 
GO
ALTER DATABASE [usedCars] SET ACCELERATED_DATABASE_RECOVERY = OFF  
GO
ALTER DATABASE [usedCars] SET QUERY_STORE = ON
GO
ALTER DATABASE [usedCars] SET QUERY_STORE (OPERATION_MODE = READ_WRITE, CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30), DATA_FLUSH_INTERVAL_SECONDS = 900, INTERVAL_LENGTH_MINUTES = 60, MAX_STORAGE_SIZE_MB = 1000, QUERY_CAPTURE_MODE = AUTO, SIZE_BASED_CLEANUP_MODE = AUTO, MAX_PLANS_PER_QUERY = 200, WAIT_STATS_CAPTURE_MODE = ON)
GO
USE [usedCars]
GO
/****** Object:  Table [dbo].[AIChatMessages]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AIChatMessages](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[session_id] [bigint] NOT NULL,
	[sender_type] [varchar](20) NOT NULL,
	[content] [nvarchar](max) NOT NULL,
	[sent_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_AIChatMessages] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[AIChatSessions]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AIChatSessions](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NULL,
	[guest_id] [nvarchar](100) NULL,
	[started_at] [datetime2](3) NOT NULL,
	[last_message_at] [datetime2](3) NULL,
 CONSTRAINT [PK_AIChatSessions] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ArticleCategories]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ArticleCategories](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](100) NOT NULL,
	[slug] [varchar](120) NOT NULL,
	[description] [nvarchar](500) NULL,
	[sort_order] [int] NOT NULL,
	[active] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
	[created_by] [bigint] NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_ArticleCategories_name] UNIQUE NONCLUSTERED 
(
	[name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_ArticleCategories_slug] UNIQUE NONCLUSTERED 
(
	[slug] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Articles]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Articles](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[title] [nvarchar](300) NOT NULL,
	[slug] [varchar](350) NOT NULL,
	[summary] [nvarchar](500) NULL,
	[content] [nvarchar](max) NOT NULL,
	[thumbnail_url] [varchar](500) NULL,
	[author_id] [bigint] NULL,
	[category_id] [bigint] NULL,
	[status] [varchar](20) NOT NULL,
	[published_at] [datetime2](7) NULL,
	[view_count] [int] NOT NULL,
	[is_deleted] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
	[created_by] [bigint] NULL,
	[is_featured] [bit] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Articles_slug] UNIQUE NONCLUSTERED 
(
	[slug] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[AuditLogs]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AuditLogs](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NULL,
	[user_name] [nvarchar](100) NULL,
	[action] [nvarchar](100) NOT NULL,
	[module] [nvarchar](50) NOT NULL,
	[details] [nvarchar](max) NULL,
	[ip_address] [nvarchar](45) NULL,
	[timestamp] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_AuditLogs] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[BookingContracts]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[BookingContracts](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[booking_id] [bigint] NOT NULL,
	[contract_status] [nvarchar](30) NOT NULL,
	[terms_version] [nvarchar](20) NOT NULL,
	[signature_type] [nvarchar](10) NULL,
	[signature_url] [nvarchar](max) NULL,
	[id_card_url] [nvarchar](500) NULL,
	[license_url] [nvarchar](500) NULL,
	[content_sha256] [nvarchar](64) NULL,
	[pdf_url] [nvarchar](500) NULL,
	[signed_at] [datetime2](7) NULL,
	[expires_at] [datetime2](7) NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[booking_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Bookings]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Bookings](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[customer_id] [bigint] NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[branch_id] [int] NOT NULL,
	[staff_id] [bigint] NULL,
	[booking_date] [date] NOT NULL,
	[time_slot] [time](7) NOT NULL,
	[note] [nvarchar](500) NULL,
	[status] [varchar](20) NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_Bookings] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[BookingSlots]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[BookingSlots](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[branch_id] [int] NOT NULL,
	[slot_time] [time](7) NOT NULL,
	[max_bookings] [int] NOT NULL,
	[is_active] [bit] NOT NULL,
 CONSTRAINT [PK_BookingSlots] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_BookingSlots_BranchTime] UNIQUE NONCLUSTERED 
(
	[branch_id] ASC,
	[slot_time] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[BookingStatusHistory]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[BookingStatusHistory](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[booking_id] [bigint] NOT NULL,
	[old_status] [varchar](20) NULL,
	[new_status] [varchar](20) NOT NULL,
	[changed_by] [bigint] NULL,
	[note] [nvarchar](500) NULL,
	[changed_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_BookingStatusHistory] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Branches]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Branches](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](200) NOT NULL,
	[address] [nvarchar](500) NOT NULL,
	[phone] [nvarchar](20) NULL,
	[lat] [decimal](10, 7) NULL,
	[lng] [decimal](10, 7) NULL,
	[status] [varchar](20) NOT NULL,
	[manager_id] [bigint] NULL,
	[is_deleted] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
	[showroom_image_urls] [nvarchar](max) NULL,
 CONSTRAINT [PK_Branches] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[BranchWorkingHours]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[BranchWorkingHours](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[branch_id] [int] NOT NULL,
	[day_of_week] [tinyint] NOT NULL,
	[open_time] [time](7) NOT NULL,
	[close_time] [time](7) NOT NULL,
	[is_closed] [bit] NOT NULL,
 CONSTRAINT [PK_BranchWorkingHours] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_BWH_BranchDay] UNIQUE NONCLUSTERED 
(
	[branch_id] ASC,
	[day_of_week] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Categories]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Categories](
	[id] [int] NOT NULL,
	[name] [nvarchar](100) NOT NULL,
	[status] [varchar](20) NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_Categories] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ChatConversations]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ChatConversations](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[title] [nvarchar](200) NULL,
	[last_message_at] [datetime2](3) NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_ChatConversations] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ChatMessages]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ChatMessages](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[conversation_id] [bigint] NOT NULL,
	[sender_id] [bigint] NOT NULL,
	[content] [nvarchar](max) NOT NULL,
	[message_type] [varchar](20) NOT NULL,
	[is_read] [bit] NOT NULL,
	[sent_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_ChatMessages] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ChatParticipants]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ChatParticipants](
	[conversation_id] [bigint] NOT NULL,
	[user_id] [bigint] NOT NULL,
	[unread_count] [int] NOT NULL,
	[joined_at] [datetime2](3) NOT NULL,
	[hidden_at] [datetime2](3) NULL,
 CONSTRAINT [PK_ChatParticipants] PRIMARY KEY CLUSTERED 
(
	[conversation_id] ASC,
	[user_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[ConsultationRoutingStates]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ConsultationRoutingStates](
	[branch_id] [int] NOT NULL,
	[last_assigned_user_id] [bigint] NULL,
	[updated_at] [datetime2](0) NOT NULL,
 CONSTRAINT [PK_ConsultationRoutingStates] PRIMARY KEY CLUSTERED 
(
	[branch_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Consultations]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Consultations](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[customer_id] [bigint] NULL,
	[customer_name] [nvarchar](100) NOT NULL,
	[customer_phone] [nvarchar](20) NOT NULL,
	[vehicle_id] [bigint] NULL,
	[message] [nvarchar](1000) NOT NULL,
	[status] [varchar](20) NOT NULL,
	[priority] [varchar](10) NOT NULL,
	[assigned_staff_id] [bigint] NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_Consultations] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Deposits]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Deposits](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[customer_id] [bigint] NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[amount] [decimal](18, 0) NOT NULL,
	[payment_method] [varchar](30) NOT NULL,
	[deposit_date] [date] NOT NULL,
	[expiry_date] [date] NOT NULL,
	[status] [varchar](20) NOT NULL,
	[order_id] [bigint] NULL,
	[notes] [nvarchar](500) NULL,
	[created_at] [datetime2](3) NOT NULL,
	[created_by] [bigint] NULL,
	[payment_gateway] [varchar](20) NULL,
	[gateway_txn_ref] [nvarchar](100) NULL,
	[gateway_trans_ref] [nvarchar](100) NULL,
	[gateway_order_url] [nvarchar](500) NULL,
 CONSTRAINT [PK_Deposits] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[DocumentSessions]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[DocumentSessions](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[session_id] [nvarchar](64) NOT NULL,
	[token_hash] [nvarchar](64) NOT NULL,
	[booking_id] [bigint] NOT NULL,
	[user_id] [bigint] NOT NULL,
	[purpose] [nvarchar](20) NOT NULL,
	[status] [nvarchar](20) NOT NULL,
	[file_url] [nvarchar](500) NULL,
	[expires_at] [datetime2](7) NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
UNIQUE NONCLUSTERED 
(
	[session_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[flyway_schema_history]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[flyway_schema_history](
	[installed_rank] [int] NOT NULL,
	[version] [nvarchar](50) NULL,
	[description] [nvarchar](200) NULL,
	[type] [nvarchar](20) NOT NULL,
	[script] [nvarchar](1000) NOT NULL,
	[checksum] [int] NULL,
	[installed_by] [nvarchar](100) NOT NULL,
	[installed_on] [datetime] NOT NULL,
	[execution_time] [int] NOT NULL,
	[success] [bit] NOT NULL,
 CONSTRAINT [flyway_schema_history_pk] PRIMARY KEY CLUSTERED 
(
	[installed_rank] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[HomePageBanners]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[HomePageBanners](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[image_url] [nvarchar](1000) NOT NULL,
	[cloudinary_public_id] [nvarchar](255) NULL,
	[sort_order] [int] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_HomePageBanners] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InstallmentApplications]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InstallmentApplications](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[customer_id] [bigint] NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[deposit_id] [bigint] NULL,
	[bank_loan_id] [nvarchar](100) NULL,
	[full_name] [nvarchar](100) NULL,
	[identity_number] [nvarchar](20) NULL,
	[phone_number] [nvarchar](20) NULL,
	[email] [nvarchar](255) NULL,
	[dob] [date] NULL,
	[identity_issued_date] [date] NULL,
	[identity_issued_place] [nvarchar](200) NULL,
	[permanent_address] [nvarchar](500) NULL,
	[current_address] [nvarchar](500) NULL,
	[employment_type] [nvarchar](100) NULL,
	[company_name] [nvarchar](200) NULL,
	[job_title] [nvarchar](100) NULL,
	[work_duration] [nvarchar](50) NULL,
	[salary_method] [nvarchar](50) NULL,
	[business_name] [nvarchar](200) NULL,
	[business_type] [nvarchar](100) NULL,
	[business_duration] [nvarchar](50) NULL,
	[monthly_income] [decimal](19, 2) NULL,
	[monthly_expenses] [decimal](19, 2) NULL,
	[existing_loans] [decimal](19, 2) NULL,
	[dependents_count] [int] NULL,
	[vehicle_price] [decimal](19, 2) NULL,
	[prepayment_amount] [decimal](19, 2) NULL,
	[loan_amount] [decimal](19, 2) NULL,
	[loan_term_months] [int] NULL,
	[repayment_method] [nvarchar](50) NULL,
	[agreed_terms] [bit] NULL,
	[agreed_privacy] [bit] NULL,
	[signature_url] [nvarchar](1000) NULL,
	[signed_date] [date] NULL,
	[status] [nvarchar](30) NOT NULL,
	[rejection_reason] [nvarchar](1000) NULL,
	[bank_pdf_url] [nvarchar](1000) NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
	[created_by] [bigint] NULL,
	[bank_code] [nvarchar](50) NULL,
	[prepayment_percent] [decimal](5, 2) NULL,
	[request_pre_deposit] [bit] NULL,
	[pre_deposit_id] [bigint] NULL,
 CONSTRAINT [PK_InstallmentApplications] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InstallmentDocuments]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InstallmentDocuments](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[application_id] [bigint] NOT NULL,
	[document_type] [nvarchar](50) NOT NULL,
	[document_url] [nvarchar](1000) NOT NULL,
	[original_file_name] [nvarchar](255) NULL,
	[uploaded_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_InstallmentDocuments] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[InstallmentStatusHistory]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[InstallmentStatusHistory](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[application_id] [bigint] NOT NULL,
	[old_status] [nvarchar](30) NULL,
	[new_status] [nvarchar](30) NOT NULL,
	[note] [nvarchar](1000) NULL,
	[changed_by] [bigint] NULL,
	[changed_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_InstallmentStatusHistory] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Notifications]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Notifications](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NOT NULL,
	[type] [varchar](30) NOT NULL,
	[title] [nvarchar](200) NOT NULL,
	[body] [nvarchar](1000) NOT NULL,
	[link] [nvarchar](500) NULL,
	[is_read] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
	[system_announcement_id] [int] NULL,
 CONSTRAINT [PK_Notifications] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[NotificationTemplates]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[NotificationTemplates](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](100) NOT NULL,
	[title_template] [nvarchar](200) NOT NULL,
	[body_template] [nvarchar](1000) NOT NULL,
	[channel] [varchar](20) NOT NULL,
 CONSTRAINT [PK_NotificationTemplates] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_NotifTpl_Name] UNIQUE NONCLUSTERED 
(
	[name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[OrderPayments]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[OrderPayments](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[order_id] [bigint] NOT NULL,
	[amount] [decimal](18, 0) NOT NULL,
	[payment_method] [varchar](30) NOT NULL,
	[status] [varchar](20) NOT NULL,
	[transaction_ref] [nvarchar](100) NULL,
	[paid_at] [datetime2](3) NULL,
	[created_at] [datetime2](3) NOT NULL,
	[vnp_pay_create_date] [varchar](14) NULL,
	[vnp_gateway_transaction_no] [nvarchar](100) NULL,
	[vnp_last_refund_request_id] [nvarchar](40) NULL,
	[last_gateway_query_json] [nvarchar](max) NULL,
	[last_gateway_query_at] [datetime2](7) NULL,
 CONSTRAINT [PK_OrderPayments] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Orders]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Orders](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[order_number] [nvarchar](20) NOT NULL,
	[customer_id] [bigint] NOT NULL,
	[staff_id] [bigint] NULL,
	[branch_id] [int] NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[total_price] [decimal](18, 0) NOT NULL,
	[deposit_amount] [decimal](18, 0) NOT NULL,
	[remaining_amount] [decimal](18, 0) NOT NULL,
	[payment_method] [varchar](30) NULL,
	[status] [varchar](20) NOT NULL,
	[notes] [nvarchar](1000) NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
	[created_by] [bigint] NULL,
 CONSTRAINT [PK_Orders] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Orders_Number] UNIQUE NONCLUSTERED 
(
	[order_number] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PasswordResetTokens]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PasswordResetTokens](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NOT NULL,
	[token] [nvarchar](128) NOT NULL,
	[expires_at] [datetime2](7) NOT NULL,
	[used] [bit] NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
 CONSTRAINT [PK_PasswordResetTokens] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_PRT_Token] UNIQUE NONCLUSTERED 
(
	[token] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[PaymentStatusHistory]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[PaymentStatusHistory](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[target_kind] [nvarchar](24) NOT NULL,
	[target_id] [bigint] NOT NULL,
	[actor_user_id] [bigint] NOT NULL,
	[from_status] [nvarchar](40) NULL,
	[to_status] [nvarchar](40) NULL,
	[action] [nvarchar](48) NOT NULL,
	[detail] [nvarchar](500) NULL,
	[created_at] [datetime2](7) NOT NULL,
 CONSTRAINT [PK_PaymentStatusHistory] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Permissions]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Permissions](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[module] [nvarchar](50) NOT NULL,
	[action] [nvarchar](50) NOT NULL,
	[description] [nvarchar](255) NULL,
 CONSTRAINT [PK_Permissions] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Permissions_ModuleAction] UNIQUE NONCLUSTERED 
(
	[module] ASC,
	[action] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RefreshTokens]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RefreshTokens](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NOT NULL,
	[token] [nvarchar](500) NOT NULL,
	[expires_at] [datetime2](3) NOT NULL,
	[is_revoked] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_RefreshTokens] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_RefreshTokens_Token] UNIQUE NONCLUSTERED 
(
	[token] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[RolePermissions]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[RolePermissions](
	[role_id] [int] NOT NULL,
	[permission_id] [int] NOT NULL,
 CONSTRAINT [PK_RolePermissions] PRIMARY KEY CLUSTERED 
(
	[role_id] ASC,
	[permission_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Roles]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Roles](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](50) NOT NULL,
	[description] [nvarchar](255) NULL,
	[is_system_role] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_Roles] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Roles_Name] UNIQUE NONCLUSTERED 
(
	[name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[SavedVehicles]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[SavedVehicles](
	[user_id] [bigint] NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[saved_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_SavedVehicles] PRIMARY KEY CLUSTERED 
(
	[user_id] ASC,
	[vehicle_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[StaffAssignments]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[StaffAssignments](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NOT NULL,
	[branch_id] [int] NOT NULL,
	[start_date] [date] NOT NULL,
	[end_date] [date] NULL,
	[is_active] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_StaffAssignments] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Subcategories]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Subcategories](
	[id] [int] NOT NULL,
	[category_id] [int] NOT NULL,
	[name] [nvarchar](200) NOT NULL,
	[name_normalized] [nvarchar](200) NULL,
	[status] [varchar](20) NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_Subcategories] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[SystemAnnouncements]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[SystemAnnouncements](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[title] [nvarchar](200) NOT NULL,
	[body] [nvarchar](2000) NOT NULL,
	[notif_kind] [varchar](20) NOT NULL,
	[audience] [varchar](30) NOT NULL,
	[target_user_ids] [nvarchar](2000) NULL,
	[published] [bit] NOT NULL,
	[send_email] [bit] NOT NULL,
	[email_sent_at] [datetime2](3) NULL,
	[email_last_error] [nvarchar](500) NULL,
	[created_by_id] [bigint] NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_SystemAnnouncements] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[SystemConfigs]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[SystemConfigs](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[config_key] [nvarchar](100) NOT NULL,
	[config_value] [nvarchar](max) NULL,
	[description] [nvarchar](500) NULL,
	[updated_at] [datetime2](3) NOT NULL,
	[updated_by] [bigint] NULL,
 CONSTRAINT [PK_SystemConfigs] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_SysConfig_Key] UNIQUE NONCLUSTERED 
(
	[config_key] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Transactions]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Transactions](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[user_id] [bigint] NOT NULL,
	[type] [varchar](20) NOT NULL,
	[payment_gateway] [varchar](20) NULL,
	[amount] [decimal](18, 0) NOT NULL,
	[description] [nvarchar](500) NULL,
	[status] [varchar](20) NOT NULL,
	[reference_id] [bigint] NULL,
	[reference_type] [varchar](30) NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_Transactions] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[TransferApprovalHistory]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[TransferApprovalHistory](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[transfer_id] [bigint] NOT NULL,
	[approved_by] [bigint] NOT NULL,
	[action] [varchar](20) NOT NULL,
	[note] [nvarchar](500) NULL,
	[acted_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_TransferApprovalHist] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[TransferRequests]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[TransferRequests](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[from_branch_id] [int] NOT NULL,
	[to_branch_id] [int] NOT NULL,
	[requested_by] [bigint] NOT NULL,
	[status] [varchar](20) NOT NULL,
	[reason] [nvarchar](500) NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_TransferRequests] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[UserRoles]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[UserRoles](
	[user_id] [bigint] NOT NULL,
	[role_id] [int] NOT NULL,
	[assigned_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_UserRoles] PRIMARY KEY CLUSTERED 
(
	[user_id] ASC,
	[role_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Users]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Users](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](100) NOT NULL,
	[email] [nvarchar](255) NOT NULL,
	[phone] [nvarchar](20) NULL,
	[password_hash] [nvarchar](255) NULL,
	[auth_provider] [varchar](50) NOT NULL,
	[provider_id] [nvarchar](255) NULL,
	[avatar_url] [nvarchar](500) NULL,
	[status] [varchar](20) NOT NULL,
	[is_deleted] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
	[created_by] [bigint] NULL,
	[address] [nvarchar](500) NULL,
	[date_of_birth] [date] NULL,
	[gender] [nvarchar](20) NULL,
	[password_change_required] [bit] NOT NULL,
 CONSTRAINT [PK_Users] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Users_Email] UNIQUE NONCLUSTERED 
(
	[email] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[VehicleFuelTypes]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[VehicleFuelTypes](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](50) NOT NULL,
	[status] [varchar](20) NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_VehicleFuelTypes] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_VehicleFuelTypes_Name] UNIQUE NONCLUSTERED 
(
	[name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[VehicleImages]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[VehicleImages](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[image_url] [nvarchar](1000) NOT NULL,
	[sort_order] [int] NOT NULL,
	[is_primary] [bit] NOT NULL,
 CONSTRAINT [PK_VehicleImages] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[VehicleMaintenanceHistory]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[VehicleMaintenanceHistory](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[maintenance_date] [date] NOT NULL,
	[description] [nvarchar](500) NOT NULL,
	[cost] [decimal](18, 0) NOT NULL,
	[performed_by] [nvarchar](200) NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_VehicleMaintenanceHistory] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[VehicleReviews]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[VehicleReviews](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[vehicle_id] [bigint] NOT NULL,
	[reviewer_id] [bigint] NOT NULL,
	[booking_id] [bigint] NOT NULL,
	[rating] [int] NOT NULL,
	[comment] [nvarchar](2000) NULL,
	[anonymous] [bit] NOT NULL,
	[status] [varchar](20) NOT NULL,
	[created_at] [datetime2](7) NOT NULL,
	[updated_at] [datetime2](7) NOT NULL,
	[created_by] [bigint] NULL,
PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_vehicle_reviewer] UNIQUE NONCLUSTERED 
(
	[vehicle_id] ASC,
	[reviewer_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[Vehicles]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Vehicles](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[listing_id] [varchar](20) NOT NULL,
	[category_id] [int] NOT NULL,
	[subcategory_id] [int] NOT NULL,
	[branch_id] [int] NOT NULL,
	[title] [nvarchar](500) NOT NULL,
	[price] [decimal](18, 0) NULL,
	[description] [nvarchar](max) NULL,
	[year] [int] NULL,
	[fuel] [nvarchar](50) NULL,
	[transmission] [nvarchar](50) NULL,
	[mileage] [int] NULL,
	[body_style] [nvarchar](50) NULL,
	[origin] [nvarchar](100) NULL,
	[posting_date] [date] NULL,
	[status] [varchar](20) NOT NULL,
	[is_deleted] [bit] NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
	[updated_at] [datetime2](3) NOT NULL,
	[created_by] [bigint] NULL,
 CONSTRAINT [PK_Vehicles] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_Vehicles_ListingId] UNIQUE NONCLUSTERED 
(
	[listing_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
/****** Object:  Table [dbo].[VehicleTransmissions]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[VehicleTransmissions](
	[id] [int] IDENTITY(1,1) NOT NULL,
	[name] [nvarchar](50) NOT NULL,
	[status] [varchar](20) NOT NULL,
	[created_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_VehicleTransmissions] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY],
 CONSTRAINT [UQ_VehicleTransmissions_Name] UNIQUE NONCLUSTERED 
(
	[name] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Table [dbo].[VehicleViewHistory]    Script Date: 03/05/2026 12:09:59 CH ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[VehicleViewHistory](
	[id] [bigint] IDENTITY(1,1) NOT NULL,
	[guest_id] [nvarchar](100) NOT NULL,
	[user_id] [bigint] NULL,
	[vehicle_id] [bigint] NOT NULL,
	[viewed_at] [datetime2](3) NOT NULL,
 CONSTRAINT [PK_VehicleViewHistory] PRIMARY KEY CLUSTERED 
(
	[id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
/****** Object:  Index [IX_AIChatMsg_SessionSentAt]    Script Date: 03/05/2026 12:09:59 CH ******/
CREATE NONCLUSTERED INDEX [IX_AIChatMsg_SessionSentAt] ON [dbo].[AIChatMessages]
(
	[session_id] ASC,
	[sent_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Articles_category_id]    Script Date: 03/05/2026 12:09:59 CH ******/
CREATE NONCLUSTERED INDEX [IX_Articles_category_id] ON [dbo].[Articles]
(
	[category_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Articles_featured_published_at]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Articles_featured_published_at] ON [dbo].[Articles]
(
	[is_featured] DESC,
	[published_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Articles_published_at]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Articles_published_at] ON [dbo].[Articles]
(
	[published_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Articles_status_deleted]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Articles_status_deleted] ON [dbo].[Articles]
(
	[status] ASC,
	[is_deleted] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_AuditLogs_Module]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_AuditLogs_Module] ON [dbo].[AuditLogs]
(
	[module] ASC,
	[timestamp] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_AuditLogs_Timestamp]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_AuditLogs_Timestamp] ON [dbo].[AuditLogs]
(
	[timestamp] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_AuditLogs_UserId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_AuditLogs_UserId] ON [dbo].[AuditLogs]
(
	[user_id] ASC
)
WHERE ([user_id] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Bookings_BranchDate]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Bookings_BranchDate] ON [dbo].[Bookings]
(
	[branch_id] ASC,
	[booking_date] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Bookings_Customer]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Bookings_Customer] ON [dbo].[Bookings]
(
	[customer_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Bookings_StaffDate]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Bookings_StaffDate] ON [dbo].[Bookings]
(
	[staff_id] ASC,
	[booking_date] ASC
)
WHERE ([staff_id] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Bookings_VehicleId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Bookings_VehicleId] ON [dbo].[Bookings]
(
	[vehicle_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [UQ_Bookings_VehicleSlot]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE UNIQUE NONCLUSTERED INDEX [UQ_Bookings_VehicleSlot] ON [dbo].[Bookings]
(
	[vehicle_id] ASC,
	[booking_date] ASC,
	[time_slot] ASC
)
WHERE ([status] IN ('Pending', 'Confirmed'))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_BSH_BookingId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_BSH_BookingId] ON [dbo].[BookingStatusHistory]
(
	[booking_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Branches_ManagerId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Branches_ManagerId] ON [dbo].[Branches]
(
	[manager_id] ASC
)
WHERE ([manager_id] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Branches_Status]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Branches_Status] ON [dbo].[Branches]
(
	[status] ASC
)
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_ChatMsg_ConvSentAt]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_ChatMsg_ConvSentAt] ON [dbo].[ChatMessages]
(
	[conversation_id] ASC,
	[sent_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_ChatPart_UserId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_ChatPart_UserId] ON [dbo].[ChatParticipants]
(
	[user_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Consult_Status]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Consult_Status] ON [dbo].[Consultations]
(
	[status] ASC,
	[priority] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Consult_Vehicle]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Consult_Vehicle] ON [dbo].[Consultations]
(
	[vehicle_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Deposits_Customer]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Deposits_Customer] ON [dbo].[Deposits]
(
	[customer_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Deposits_Expiry]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Deposits_Expiry] ON [dbo].[Deposits]
(
	[expiry_date] ASC,
	[status] ASC,
	[vehicle_id] ASC
)
WHERE ([status]='CONFIRMED')
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Deposits_Vehicle]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Deposits_Vehicle] ON [dbo].[Deposits]
(
	[vehicle_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [flyway_schema_history_s_idx]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [flyway_schema_history_s_idx] ON [dbo].[flyway_schema_history]
(
	[success] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_InstApp_Customer]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_InstApp_Customer] ON [dbo].[InstallmentApplications]
(
	[customer_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_InstApp_Vehicle]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_InstApp_Vehicle] ON [dbo].[InstallmentApplications]
(
	[vehicle_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_InstDoc_Application]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_InstDoc_Application] ON [dbo].[InstallmentDocuments]
(
	[application_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_InstStatusHistory_Application]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_InstStatusHistory_Application] ON [dbo].[InstallmentStatusHistory]
(
	[application_id] ASC,
	[changed_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Notif_UserRead]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Notif_UserRead] ON [dbo].[Notifications]
(
	[user_id] ASC,
	[is_read] ASC,
	[created_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_OrderPayments_OrderId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_OrderPayments_OrderId] ON [dbo].[OrderPayments]
(
	[order_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Orders_Branch]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Orders_Branch] ON [dbo].[Orders]
(
	[branch_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Orders_CreatedAt]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Orders_CreatedAt] ON [dbo].[Orders]
(
	[created_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Orders_Customer]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Orders_Customer] ON [dbo].[Orders]
(
	[customer_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Orders_Staff]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Orders_Staff] ON [dbo].[Orders]
(
	[staff_id] ASC
)
WHERE ([staff_id] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Orders_Vehicle]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Orders_Vehicle] ON [dbo].[Orders]
(
	[vehicle_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_PRT_ExpiresAt]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_PRT_ExpiresAt] ON [dbo].[PasswordResetTokens]
(
	[expires_at] ASC
)
WHERE ([used]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_PRT_UserId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_PRT_UserId] ON [dbo].[PasswordResetTokens]
(
	[user_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_RefreshTokens_ExpiresAt]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_RefreshTokens_ExpiresAt] ON [dbo].[RefreshTokens]
(
	[expires_at] ASC
)
WHERE ([is_revoked]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_RefreshTokens_UserId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_RefreshTokens_UserId] ON [dbo].[RefreshTokens]
(
	[user_id] ASC
)
WHERE ([is_revoked]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_SavedVehicles_VehicleId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_SavedVehicles_VehicleId] ON [dbo].[SavedVehicles]
(
	[vehicle_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_StaffAssign_Active]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_StaffAssign_Active] ON [dbo].[StaffAssignments]
(
	[user_id] ASC,
	[branch_id] ASC
)
WHERE ([is_active]=(1))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_StaffAssign_BranchId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_StaffAssign_BranchId] ON [dbo].[StaffAssignments]
(
	[branch_id] ASC
)
WHERE ([is_active]=(1))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_SysAnn_CreatedAt]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_SysAnn_CreatedAt] ON [dbo].[SystemAnnouncements]
(
	[created_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Trans_Reference]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Trans_Reference] ON [dbo].[Transactions]
(
	[reference_type] ASC,
	[reference_id] ASC
)
WHERE ([reference_id] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Trans_Type]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Trans_Type] ON [dbo].[Transactions]
(
	[type] ASC,
	[created_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Trans_UserId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Trans_UserId] ON [dbo].[Transactions]
(
	[user_id] ASC,
	[created_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_TAH_TransferId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_TAH_TransferId] ON [dbo].[TransferApprovalHistory]
(
	[transfer_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Transfer_FromBranch]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Transfer_FromBranch] ON [dbo].[TransferRequests]
(
	[from_branch_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Transfer_Status]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Transfer_Status] ON [dbo].[TransferRequests]
(
	[status] ASC,
	[created_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Transfer_ToBranch]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Transfer_ToBranch] ON [dbo].[TransferRequests]
(
	[to_branch_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_TransferRequests_VehicleActive]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_TransferRequests_VehicleActive] ON [dbo].[TransferRequests]
(
	[vehicle_id] ASC,
	[status] ASC
)
WHERE ([status] IN ('Pending', 'Approved'))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Users_Email]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Users_Email] ON [dbo].[Users]
(
	[email] ASC
)
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Users_Phone]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Users_Phone] ON [dbo].[Users]
(
	[phone] ASC
)
WHERE ([phone] IS NOT NULL AND [is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Users_Status]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Users_Status] ON [dbo].[Users]
(
	[status] ASC
)
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_VehicleImages_VehicleId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VehicleImages_VehicleId] ON [dbo].[VehicleImages]
(
	[vehicle_id] ASC,
	[sort_order] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_VMH_VehicleId]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VMH_VehicleId] ON [dbo].[VehicleMaintenanceHistory]
(
	[vehicle_id] ASC,
	[maintenance_date] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_VehicleReviews_reviewer]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VehicleReviews_reviewer] ON [dbo].[VehicleReviews]
(
	[reviewer_id] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_VehicleReviews_vehicle_status]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VehicleReviews_vehicle_status] ON [dbo].[VehicleReviews]
(
	[vehicle_id] ASC,
	[status] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Vehicles_BranchStatus]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Vehicles_BranchStatus] ON [dbo].[Vehicles]
(
	[branch_id] ASC,
	[status] ASC
)
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Vehicles_CatSubcat]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Vehicles_CatSubcat] ON [dbo].[Vehicles]
(
	[category_id] ASC,
	[subcategory_id] ASC
)
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Vehicles_Price]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Vehicles_Price] ON [dbo].[Vehicles]
(
	[price] ASC
)
WHERE ([is_deleted]=(0) AND [status]='Available')
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_Vehicles_Search]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Vehicles_Search] ON [dbo].[Vehicles]
(
	[status] ASC,
	[branch_id] ASC,
	[category_id] ASC,
	[price] ASC,
	[year] ASC
)
INCLUDE([subcategory_id],[mileage],[fuel],[transmission]) 
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_Vehicles_Year]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_Vehicles_Year] ON [dbo].[Vehicles]
(
	[year] ASC
)
WHERE ([is_deleted]=(0))
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_VViewHistory_GuestMerge]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VViewHistory_GuestMerge] ON [dbo].[VehicleViewHistory]
(
	[guest_id] ASC
)
WHERE ([user_id] IS NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
SET ANSI_PADDING ON
GO
/****** Object:  Index [IX_VViewHistory_GuestRecent]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VViewHistory_GuestRecent] ON [dbo].[VehicleViewHistory]
(
	[guest_id] ASC,
	[viewed_at] DESC
)
INCLUDE([vehicle_id],[user_id]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_VViewHistory_UserRecent]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VViewHistory_UserRecent] ON [dbo].[VehicleViewHistory]
(
	[user_id] ASC,
	[viewed_at] DESC
)
INCLUDE([vehicle_id],[guest_id]) 
WHERE ([user_id] IS NOT NULL)
WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
/****** Object:  Index [IX_VViewHistory_VehicleAnalytics]    Script Date: 03/05/2026 12:10:00 CH ******/
CREATE NONCLUSTERED INDEX [IX_VViewHistory_VehicleAnalytics] ON [dbo].[VehicleViewHistory]
(
	[vehicle_id] ASC,
	[viewed_at] DESC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO
ALTER TABLE [dbo].[AIChatMessages] ADD  CONSTRAINT [DF_AIChatMsg_SentAt]  DEFAULT (sysutcdatetime()) FOR [sent_at]
GO
ALTER TABLE [dbo].[AIChatSessions] ADD  CONSTRAINT [DF_AIChat_StartedAt]  DEFAULT (sysutcdatetime()) FOR [started_at]
GO
ALTER TABLE [dbo].[ArticleCategories] ADD  DEFAULT ((0)) FOR [sort_order]
GO
ALTER TABLE [dbo].[ArticleCategories] ADD  DEFAULT ((1)) FOR [active]
GO
ALTER TABLE [dbo].[ArticleCategories] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[ArticleCategories] ADD  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Articles] ADD  DEFAULT ('draft') FOR [status]
GO
ALTER TABLE [dbo].[Articles] ADD  DEFAULT ((0)) FOR [view_count]
GO
ALTER TABLE [dbo].[Articles] ADD  DEFAULT ((0)) FOR [is_deleted]
GO
ALTER TABLE [dbo].[Articles] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Articles] ADD  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Articles] ADD  CONSTRAINT [DF_Articles_is_featured]  DEFAULT ((0)) FOR [is_featured]
GO
ALTER TABLE [dbo].[AuditLogs] ADD  CONSTRAINT [DF_AuditLogs_Timestamp]  DEFAULT (sysutcdatetime()) FOR [timestamp]
GO
ALTER TABLE [dbo].[BookingContracts] ADD  DEFAULT ('PENDING_SIGNATURE') FOR [contract_status]
GO
ALTER TABLE [dbo].[BookingContracts] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[BookingContracts] ADD  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Bookings] ADD  CONSTRAINT [DF_Bookings_Status]  DEFAULT ('Pending') FOR [status]
GO
ALTER TABLE [dbo].[Bookings] ADD  CONSTRAINT [DF_Bookings_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Bookings] ADD  CONSTRAINT [DF_Bookings_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[BookingSlots] ADD  CONSTRAINT [DF_BookingSlots_Max]  DEFAULT ((3)) FOR [max_bookings]
GO
ALTER TABLE [dbo].[BookingSlots] ADD  CONSTRAINT [DF_BookingSlots_IsActive]  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[BookingStatusHistory] ADD  CONSTRAINT [DF_BSH_ChangedAt]  DEFAULT (sysutcdatetime()) FOR [changed_at]
GO
ALTER TABLE [dbo].[Branches] ADD  CONSTRAINT [DF_Branches_Status]  DEFAULT ('active') FOR [status]
GO
ALTER TABLE [dbo].[Branches] ADD  CONSTRAINT [DF_Branches_IsDeleted]  DEFAULT ((0)) FOR [is_deleted]
GO
ALTER TABLE [dbo].[Branches] ADD  CONSTRAINT [DF_Branches_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Branches] ADD  CONSTRAINT [DF_Branches_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[BranchWorkingHours] ADD  CONSTRAINT [DF_BWH_IsClosed]  DEFAULT ((0)) FOR [is_closed]
GO
ALTER TABLE [dbo].[Categories] ADD  CONSTRAINT [DF_Categories_Status]  DEFAULT ('active') FOR [status]
GO
ALTER TABLE [dbo].[Categories] ADD  CONSTRAINT [DF_Categories_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[ChatConversations] ADD  CONSTRAINT [DF_ChatConv_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[ChatMessages] ADD  CONSTRAINT [DF_ChatMsg_Type]  DEFAULT ('text') FOR [message_type]
GO
ALTER TABLE [dbo].[ChatMessages] ADD  CONSTRAINT [DF_ChatMsg_IsRead]  DEFAULT ((0)) FOR [is_read]
GO
ALTER TABLE [dbo].[ChatMessages] ADD  CONSTRAINT [DF_ChatMsg_SentAt]  DEFAULT (sysutcdatetime()) FOR [sent_at]
GO
ALTER TABLE [dbo].[ChatParticipants] ADD  CONSTRAINT [DF_ChatPart_Unread]  DEFAULT ((0)) FOR [unread_count]
GO
ALTER TABLE [dbo].[ChatParticipants] ADD  CONSTRAINT [DF_ChatPart_JoinedAt]  DEFAULT (sysutcdatetime()) FOR [joined_at]
GO
ALTER TABLE [dbo].[ConsultationRoutingStates] ADD  CONSTRAINT [DF_ConsultRouting_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Consultations] ADD  CONSTRAINT [DF_Consult_Status]  DEFAULT ('pending') FOR [status]
GO
ALTER TABLE [dbo].[Consultations] ADD  CONSTRAINT [DF_Consult_Priority]  DEFAULT ('medium') FOR [priority]
GO
ALTER TABLE [dbo].[Consultations] ADD  CONSTRAINT [DF_Consult_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Consultations] ADD  CONSTRAINT [DF_Consult_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Deposits] ADD  CONSTRAINT [DF_Deposits_Status]  DEFAULT ('Pending') FOR [status]
GO
ALTER TABLE [dbo].[Deposits] ADD  CONSTRAINT [DF_Deposits_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[DocumentSessions] ADD  DEFAULT ('WAITING') FOR [status]
GO
ALTER TABLE [dbo].[DocumentSessions] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[flyway_schema_history] ADD  DEFAULT (getdate()) FOR [installed_on]
GO
ALTER TABLE [dbo].[HomePageBanners] ADD  CONSTRAINT [DF_HomePageBanners_Sort]  DEFAULT ((0)) FOR [sort_order]
GO
ALTER TABLE [dbo].[HomePageBanners] ADD  CONSTRAINT [DF_HomePageBanners_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[InstallmentApplications] ADD  CONSTRAINT [DF_InstallmentApplications_Status]  DEFAULT (N'DRAFT') FOR [status]
GO
ALTER TABLE [dbo].[InstallmentApplications] ADD  CONSTRAINT [DF_InstallmentApplications_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[InstallmentApplications] ADD  CONSTRAINT [DF_InstallmentApplications_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[InstallmentDocuments] ADD  CONSTRAINT [DF_InstallmentDocuments_UploadedAt]  DEFAULT (sysutcdatetime()) FOR [uploaded_at]
GO
ALTER TABLE [dbo].[InstallmentStatusHistory] ADD  CONSTRAINT [DF_InstallmentStatusHistory_ChangedAt]  DEFAULT (sysutcdatetime()) FOR [changed_at]
GO
ALTER TABLE [dbo].[Notifications] ADD  CONSTRAINT [DF_Notif_IsRead]  DEFAULT ((0)) FOR [is_read]
GO
ALTER TABLE [dbo].[Notifications] ADD  CONSTRAINT [DF_Notif_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[NotificationTemplates] ADD  CONSTRAINT [DF_NotifTpl_Channel]  DEFAULT ('in_app') FOR [channel]
GO
ALTER TABLE [dbo].[OrderPayments] ADD  CONSTRAINT [DF_OrderPay_Status]  DEFAULT ('Pending') FOR [status]
GO
ALTER TABLE [dbo].[OrderPayments] ADD  CONSTRAINT [DF_OrderPay_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Orders] ADD  CONSTRAINT [DF_Orders_Deposit]  DEFAULT ((0)) FOR [deposit_amount]
GO
ALTER TABLE [dbo].[Orders] ADD  CONSTRAINT [DF_Orders_Status]  DEFAULT ('Pending') FOR [status]
GO
ALTER TABLE [dbo].[Orders] ADD  CONSTRAINT [DF_Orders_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Orders] ADD  CONSTRAINT [DF_Orders_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[PasswordResetTokens] ADD  CONSTRAINT [DF_PRT_Used]  DEFAULT ((0)) FOR [used]
GO
ALTER TABLE [dbo].[PasswordResetTokens] ADD  CONSTRAINT [DF_PRT_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[RefreshTokens] ADD  CONSTRAINT [DF_RefreshTokens_IsRevoked]  DEFAULT ((0)) FOR [is_revoked]
GO
ALTER TABLE [dbo].[RefreshTokens] ADD  CONSTRAINT [DF_RefreshTokens_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Roles] ADD  CONSTRAINT [DF_Roles_IsSystem]  DEFAULT ((0)) FOR [is_system_role]
GO
ALTER TABLE [dbo].[Roles] ADD  CONSTRAINT [DF_Roles_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[SavedVehicles] ADD  CONSTRAINT [DF_SavedVehicles_SavedAt]  DEFAULT (sysutcdatetime()) FOR [saved_at]
GO
ALTER TABLE [dbo].[StaffAssignments] ADD  CONSTRAINT [DF_StaffAssign_IsActive]  DEFAULT ((1)) FOR [is_active]
GO
ALTER TABLE [dbo].[StaffAssignments] ADD  CONSTRAINT [DF_StaffAssign_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Subcategories] ADD  CONSTRAINT [DF_Subcategories_Status]  DEFAULT ('active') FOR [status]
GO
ALTER TABLE [dbo].[Subcategories] ADD  CONSTRAINT [DF_Subcategories_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[SystemAnnouncements] ADD  CONSTRAINT [DF_SysAnn_Aud]  DEFAULT ('NONE') FOR [audience]
GO
ALTER TABLE [dbo].[SystemAnnouncements] ADD  CONSTRAINT [DF_SysAnn_Pub]  DEFAULT ((0)) FOR [published]
GO
ALTER TABLE [dbo].[SystemAnnouncements] ADD  CONSTRAINT [DF_SysAnn_Email]  DEFAULT ((0)) FOR [send_email]
GO
ALTER TABLE [dbo].[SystemAnnouncements] ADD  CONSTRAINT [DF_SysAnn_CAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[SystemAnnouncements] ADD  CONSTRAINT [DF_SysAnn_UAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[SystemConfigs] ADD  CONSTRAINT [DF_SysConfig_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Transactions] ADD  CONSTRAINT [DF_Trans_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[TransferApprovalHistory] ADD  CONSTRAINT [DF_TAH_ActedAt]  DEFAULT (sysutcdatetime()) FOR [acted_at]
GO
ALTER TABLE [dbo].[TransferRequests] ADD  CONSTRAINT [DF_Transfer_Status]  DEFAULT ('Pending') FOR [status]
GO
ALTER TABLE [dbo].[TransferRequests] ADD  CONSTRAINT [DF_Transfer_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[TransferRequests] ADD  CONSTRAINT [DF_Transfer_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[UserRoles] ADD  CONSTRAINT [DF_UserRoles_AssignedAt]  DEFAULT (sysutcdatetime()) FOR [assigned_at]
GO
ALTER TABLE [dbo].[Users] ADD  CONSTRAINT [DF_Users_AuthProv]  DEFAULT ('local') FOR [auth_provider]
GO
ALTER TABLE [dbo].[Users] ADD  CONSTRAINT [DF_Users_Status]  DEFAULT ('active') FOR [status]
GO
ALTER TABLE [dbo].[Users] ADD  CONSTRAINT [DF_Users_IsDeleted]  DEFAULT ((0)) FOR [is_deleted]
GO
ALTER TABLE [dbo].[Users] ADD  CONSTRAINT [DF_Users_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Users] ADD  CONSTRAINT [DF_Users_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Users] ADD  DEFAULT ((0)) FOR [password_change_required]
GO
ALTER TABLE [dbo].[VehicleFuelTypes] ADD  CONSTRAINT [DF_VehicleFuelTypes_Status]  DEFAULT ('active') FOR [status]
GO
ALTER TABLE [dbo].[VehicleFuelTypes] ADD  CONSTRAINT [DF_VehicleFuelTypes_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[VehicleImages] ADD  CONSTRAINT [DF_VImages_SortOrder]  DEFAULT ((0)) FOR [sort_order]
GO
ALTER TABLE [dbo].[VehicleImages] ADD  CONSTRAINT [DF_VImages_IsPrimary]  DEFAULT ((0)) FOR [is_primary]
GO
ALTER TABLE [dbo].[VehicleMaintenanceHistory] ADD  CONSTRAINT [DF_VMH_Cost]  DEFAULT ((0)) FOR [cost]
GO
ALTER TABLE [dbo].[VehicleMaintenanceHistory] ADD  CONSTRAINT [DF_VMH_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[VehicleReviews] ADD  DEFAULT ((0)) FOR [anonymous]
GO
ALTER TABLE [dbo].[VehicleReviews] ADD  DEFAULT ('pending') FOR [status]
GO
ALTER TABLE [dbo].[VehicleReviews] ADD  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[VehicleReviews] ADD  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[Vehicles] ADD  CONSTRAINT [DF_Vehicles_Mileage]  DEFAULT ((0)) FOR [mileage]
GO
ALTER TABLE [dbo].[Vehicles] ADD  CONSTRAINT [DF_Vehicles_Status]  DEFAULT ('Available') FOR [status]
GO
ALTER TABLE [dbo].[Vehicles] ADD  CONSTRAINT [DF_Vehicles_IsDeleted]  DEFAULT ((0)) FOR [is_deleted]
GO
ALTER TABLE [dbo].[Vehicles] ADD  CONSTRAINT [DF_Vehicles_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[Vehicles] ADD  CONSTRAINT [DF_Vehicles_UpdatedAt]  DEFAULT (sysutcdatetime()) FOR [updated_at]
GO
ALTER TABLE [dbo].[VehicleTransmissions] ADD  CONSTRAINT [DF_VehicleTransmissions_Status]  DEFAULT ('active') FOR [status]
GO
ALTER TABLE [dbo].[VehicleTransmissions] ADD  CONSTRAINT [DF_VehicleTransmissions_CreatedAt]  DEFAULT (sysutcdatetime()) FOR [created_at]
GO
ALTER TABLE [dbo].[VehicleViewHistory] ADD  CONSTRAINT [DF_VViewHistory_ViewedAt]  DEFAULT (sysutcdatetime()) FOR [viewed_at]
GO
ALTER TABLE [dbo].[AIChatMessages]  WITH CHECK ADD  CONSTRAINT [FK_AIChatMsg_Session] FOREIGN KEY([session_id])
REFERENCES [dbo].[AIChatSessions] ([id])
GO
ALTER TABLE [dbo].[AIChatMessages] CHECK CONSTRAINT [FK_AIChatMsg_Session]
GO
ALTER TABLE [dbo].[AIChatSessions]  WITH CHECK ADD  CONSTRAINT [FK_AIChat_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[AIChatSessions] CHECK CONSTRAINT [FK_AIChat_User]
GO
ALTER TABLE [dbo].[Articles]  WITH CHECK ADD  CONSTRAINT [FK_Articles_author] FOREIGN KEY([author_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Articles] CHECK CONSTRAINT [FK_Articles_author]
GO
ALTER TABLE [dbo].[Articles]  WITH CHECK ADD  CONSTRAINT [FK_Articles_category] FOREIGN KEY([category_id])
REFERENCES [dbo].[ArticleCategories] ([id])
GO
ALTER TABLE [dbo].[Articles] CHECK CONSTRAINT [FK_Articles_category]
GO
ALTER TABLE [dbo].[AuditLogs]  WITH CHECK ADD  CONSTRAINT [FK_AuditLogs_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[AuditLogs] CHECK CONSTRAINT [FK_AuditLogs_User]
GO
ALTER TABLE [dbo].[BookingContracts]  WITH CHECK ADD  CONSTRAINT [FK_BookingContracts_Bookings] FOREIGN KEY([booking_id])
REFERENCES [dbo].[Bookings] ([id])
GO
ALTER TABLE [dbo].[BookingContracts] CHECK CONSTRAINT [FK_BookingContracts_Bookings]
GO
ALTER TABLE [dbo].[Bookings]  WITH CHECK ADD  CONSTRAINT [FK_Bookings_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[Bookings] CHECK CONSTRAINT [FK_Bookings_Branch]
GO
ALTER TABLE [dbo].[Bookings]  WITH CHECK ADD  CONSTRAINT [FK_Bookings_Customer] FOREIGN KEY([customer_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Bookings] CHECK CONSTRAINT [FK_Bookings_Customer]
GO
ALTER TABLE [dbo].[Bookings]  WITH CHECK ADD  CONSTRAINT [FK_Bookings_Staff] FOREIGN KEY([staff_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Bookings] CHECK CONSTRAINT [FK_Bookings_Staff]
GO
ALTER TABLE [dbo].[Bookings]  WITH CHECK ADD  CONSTRAINT [FK_Bookings_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[Bookings] CHECK CONSTRAINT [FK_Bookings_Vehicle]
GO
ALTER TABLE [dbo].[BookingSlots]  WITH CHECK ADD  CONSTRAINT [FK_BookingSlots_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[BookingSlots] CHECK CONSTRAINT [FK_BookingSlots_Branch]
GO
ALTER TABLE [dbo].[BookingStatusHistory]  WITH CHECK ADD  CONSTRAINT [FK_BSH_Booking] FOREIGN KEY([booking_id])
REFERENCES [dbo].[Bookings] ([id])
GO
ALTER TABLE [dbo].[BookingStatusHistory] CHECK CONSTRAINT [FK_BSH_Booking]
GO
ALTER TABLE [dbo].[BookingStatusHistory]  WITH CHECK ADD  CONSTRAINT [FK_BSH_ChangedBy] FOREIGN KEY([changed_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[BookingStatusHistory] CHECK CONSTRAINT [FK_BSH_ChangedBy]
GO
ALTER TABLE [dbo].[Branches]  WITH CHECK ADD  CONSTRAINT [FK_Branches_Manager] FOREIGN KEY([manager_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Branches] CHECK CONSTRAINT [FK_Branches_Manager]
GO
ALTER TABLE [dbo].[BranchWorkingHours]  WITH CHECK ADD  CONSTRAINT [FK_BWH_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[BranchWorkingHours] CHECK CONSTRAINT [FK_BWH_Branch]
GO
ALTER TABLE [dbo].[ChatMessages]  WITH CHECK ADD  CONSTRAINT [FK_ChatMsg_Conv] FOREIGN KEY([conversation_id])
REFERENCES [dbo].[ChatConversations] ([id])
GO
ALTER TABLE [dbo].[ChatMessages] CHECK CONSTRAINT [FK_ChatMsg_Conv]
GO
ALTER TABLE [dbo].[ChatMessages]  WITH CHECK ADD  CONSTRAINT [FK_ChatMsg_Sender] FOREIGN KEY([sender_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[ChatMessages] CHECK CONSTRAINT [FK_ChatMsg_Sender]
GO
ALTER TABLE [dbo].[ChatParticipants]  WITH CHECK ADD  CONSTRAINT [FK_ChatPart_Conv] FOREIGN KEY([conversation_id])
REFERENCES [dbo].[ChatConversations] ([id])
GO
ALTER TABLE [dbo].[ChatParticipants] CHECK CONSTRAINT [FK_ChatPart_Conv]
GO
ALTER TABLE [dbo].[ChatParticipants]  WITH CHECK ADD  CONSTRAINT [FK_ChatPart_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[ChatParticipants] CHECK CONSTRAINT [FK_ChatPart_User]
GO
ALTER TABLE [dbo].[ConsultationRoutingStates]  WITH CHECK ADD  CONSTRAINT [FK_ConsultRouting_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[ConsultationRoutingStates] CHECK CONSTRAINT [FK_ConsultRouting_Branch]
GO
ALTER TABLE [dbo].[ConsultationRoutingStates]  WITH CHECK ADD  CONSTRAINT [FK_ConsultRouting_User] FOREIGN KEY([last_assigned_user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[ConsultationRoutingStates] CHECK CONSTRAINT [FK_ConsultRouting_User]
GO
ALTER TABLE [dbo].[Consultations]  WITH CHECK ADD  CONSTRAINT [FK_Consult_Customer] FOREIGN KEY([customer_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Consultations] CHECK CONSTRAINT [FK_Consult_Customer]
GO
ALTER TABLE [dbo].[Consultations]  WITH CHECK ADD  CONSTRAINT [FK_Consult_Staff] FOREIGN KEY([assigned_staff_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Consultations] CHECK CONSTRAINT [FK_Consult_Staff]
GO
ALTER TABLE [dbo].[Consultations]  WITH CHECK ADD  CONSTRAINT [FK_Consult_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[Consultations] CHECK CONSTRAINT [FK_Consult_Vehicle]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [FK_Deposits_CreatedBy] FOREIGN KEY([created_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [FK_Deposits_CreatedBy]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [FK_Deposits_Customer] FOREIGN KEY([customer_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [FK_Deposits_Customer]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [FK_Deposits_Order] FOREIGN KEY([order_id])
REFERENCES [dbo].[Orders] ([id])
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [FK_Deposits_Order]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [FK_Deposits_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [FK_Deposits_Vehicle]
GO
ALTER TABLE [dbo].[DocumentSessions]  WITH CHECK ADD  CONSTRAINT [FK_DocumentSessions_Bookings] FOREIGN KEY([booking_id])
REFERENCES [dbo].[Bookings] ([id])
GO
ALTER TABLE [dbo].[DocumentSessions] CHECK CONSTRAINT [FK_DocumentSessions_Bookings]
GO
ALTER TABLE [dbo].[InstallmentApplications]  WITH CHECK ADD  CONSTRAINT [FK_installment_pre_deposit] FOREIGN KEY([pre_deposit_id])
REFERENCES [dbo].[Deposits] ([id])
GO
ALTER TABLE [dbo].[InstallmentApplications] CHECK CONSTRAINT [FK_installment_pre_deposit]
GO
ALTER TABLE [dbo].[InstallmentApplications]  WITH CHECK ADD  CONSTRAINT [FK_InstallmentApplications_Customer] FOREIGN KEY([customer_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[InstallmentApplications] CHECK CONSTRAINT [FK_InstallmentApplications_Customer]
GO
ALTER TABLE [dbo].[InstallmentApplications]  WITH CHECK ADD  CONSTRAINT [FK_InstallmentApplications_Deposit] FOREIGN KEY([deposit_id])
REFERENCES [dbo].[Deposits] ([id])
GO
ALTER TABLE [dbo].[InstallmentApplications] CHECK CONSTRAINT [FK_InstallmentApplications_Deposit]
GO
ALTER TABLE [dbo].[InstallmentApplications]  WITH CHECK ADD  CONSTRAINT [FK_InstallmentApplications_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[InstallmentApplications] CHECK CONSTRAINT [FK_InstallmentApplications_Vehicle]
GO
ALTER TABLE [dbo].[InstallmentDocuments]  WITH CHECK ADD  CONSTRAINT [FK_InstallmentDocuments_Application] FOREIGN KEY([application_id])
REFERENCES [dbo].[InstallmentApplications] ([id])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[InstallmentDocuments] CHECK CONSTRAINT [FK_InstallmentDocuments_Application]
GO
ALTER TABLE [dbo].[InstallmentStatusHistory]  WITH CHECK ADD  CONSTRAINT [FK_InstallmentStatusHistory_Application] FOREIGN KEY([application_id])
REFERENCES [dbo].[InstallmentApplications] ([id])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[InstallmentStatusHistory] CHECK CONSTRAINT [FK_InstallmentStatusHistory_Application]
GO
ALTER TABLE [dbo].[InstallmentStatusHistory]  WITH CHECK ADD  CONSTRAINT [FK_InstallmentStatusHistory_ChangedBy] FOREIGN KEY([changed_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[InstallmentStatusHistory] CHECK CONSTRAINT [FK_InstallmentStatusHistory_ChangedBy]
GO
ALTER TABLE [dbo].[Notifications]  WITH CHECK ADD  CONSTRAINT [FK_Notif_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Notifications] CHECK CONSTRAINT [FK_Notif_User]
GO
ALTER TABLE [dbo].[Notifications]  WITH CHECK ADD  CONSTRAINT [FK_Notifications_SystemAnnouncements] FOREIGN KEY([system_announcement_id])
REFERENCES [dbo].[SystemAnnouncements] ([id])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[Notifications] CHECK CONSTRAINT [FK_Notifications_SystemAnnouncements]
GO
ALTER TABLE [dbo].[OrderPayments]  WITH CHECK ADD  CONSTRAINT [FK_OrderPay_Order] FOREIGN KEY([order_id])
REFERENCES [dbo].[Orders] ([id])
GO
ALTER TABLE [dbo].[OrderPayments] CHECK CONSTRAINT [FK_OrderPay_Order]
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD  CONSTRAINT [FK_Orders_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[Orders] CHECK CONSTRAINT [FK_Orders_Branch]
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD  CONSTRAINT [FK_Orders_CreatedBy] FOREIGN KEY([created_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Orders] CHECK CONSTRAINT [FK_Orders_CreatedBy]
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD  CONSTRAINT [FK_Orders_Customer] FOREIGN KEY([customer_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Orders] CHECK CONSTRAINT [FK_Orders_Customer]
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD  CONSTRAINT [FK_Orders_Staff] FOREIGN KEY([staff_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Orders] CHECK CONSTRAINT [FK_Orders_Staff]
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD  CONSTRAINT [FK_Orders_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[Orders] CHECK CONSTRAINT [FK_Orders_Vehicle]
GO
ALTER TABLE [dbo].[PasswordResetTokens]  WITH CHECK ADD  CONSTRAINT [FK_PRT_UserId] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[PasswordResetTokens] CHECK CONSTRAINT [FK_PRT_UserId]
GO
ALTER TABLE [dbo].[RefreshTokens]  WITH CHECK ADD  CONSTRAINT [FK_RefreshTokens_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[RefreshTokens] CHECK CONSTRAINT [FK_RefreshTokens_User]
GO
ALTER TABLE [dbo].[RolePermissions]  WITH CHECK ADD  CONSTRAINT [FK_RolePermissions_Permission] FOREIGN KEY([permission_id])
REFERENCES [dbo].[Permissions] ([id])
GO
ALTER TABLE [dbo].[RolePermissions] CHECK CONSTRAINT [FK_RolePermissions_Permission]
GO
ALTER TABLE [dbo].[RolePermissions]  WITH CHECK ADD  CONSTRAINT [FK_RolePermissions_Role] FOREIGN KEY([role_id])
REFERENCES [dbo].[Roles] ([id])
GO
ALTER TABLE [dbo].[RolePermissions] CHECK CONSTRAINT [FK_RolePermissions_Role]
GO
ALTER TABLE [dbo].[SavedVehicles]  WITH CHECK ADD  CONSTRAINT [FK_SavedVehicles_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[SavedVehicles] CHECK CONSTRAINT [FK_SavedVehicles_User]
GO
ALTER TABLE [dbo].[SavedVehicles]  WITH CHECK ADD  CONSTRAINT [FK_SavedVehicles_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[SavedVehicles] CHECK CONSTRAINT [FK_SavedVehicles_Vehicle]
GO
ALTER TABLE [dbo].[StaffAssignments]  WITH CHECK ADD  CONSTRAINT [FK_StaffAssign_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[StaffAssignments] CHECK CONSTRAINT [FK_StaffAssign_Branch]
GO
ALTER TABLE [dbo].[StaffAssignments]  WITH CHECK ADD  CONSTRAINT [FK_StaffAssign_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[StaffAssignments] CHECK CONSTRAINT [FK_StaffAssign_User]
GO
ALTER TABLE [dbo].[Subcategories]  WITH CHECK ADD  CONSTRAINT [FK_Subcategories_Category] FOREIGN KEY([category_id])
REFERENCES [dbo].[Categories] ([id])
GO
ALTER TABLE [dbo].[Subcategories] CHECK CONSTRAINT [FK_Subcategories_Category]
GO
ALTER TABLE [dbo].[SystemAnnouncements]  WITH CHECK ADD  CONSTRAINT [FK_SysAnn_Creator] FOREIGN KEY([created_by_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[SystemAnnouncements] CHECK CONSTRAINT [FK_SysAnn_Creator]
GO
ALTER TABLE [dbo].[SystemConfigs]  WITH CHECK ADD  CONSTRAINT [FK_SysConfig_UpdatedBy] FOREIGN KEY([updated_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[SystemConfigs] CHECK CONSTRAINT [FK_SysConfig_UpdatedBy]
GO
ALTER TABLE [dbo].[Transactions]  WITH CHECK ADD  CONSTRAINT [FK_Trans_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Transactions] CHECK CONSTRAINT [FK_Trans_User]
GO
ALTER TABLE [dbo].[TransferApprovalHistory]  WITH CHECK ADD  CONSTRAINT [FK_TAH_ApprovedBy] FOREIGN KEY([approved_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[TransferApprovalHistory] CHECK CONSTRAINT [FK_TAH_ApprovedBy]
GO
ALTER TABLE [dbo].[TransferApprovalHistory]  WITH CHECK ADD  CONSTRAINT [FK_TAH_Transfer] FOREIGN KEY([transfer_id])
REFERENCES [dbo].[TransferRequests] ([id])
GO
ALTER TABLE [dbo].[TransferApprovalHistory] CHECK CONSTRAINT [FK_TAH_Transfer]
GO
ALTER TABLE [dbo].[TransferRequests]  WITH CHECK ADD  CONSTRAINT [FK_Transfer_FromBranch] FOREIGN KEY([from_branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[TransferRequests] CHECK CONSTRAINT [FK_Transfer_FromBranch]
GO
ALTER TABLE [dbo].[TransferRequests]  WITH CHECK ADD  CONSTRAINT [FK_Transfer_RequestedBy] FOREIGN KEY([requested_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[TransferRequests] CHECK CONSTRAINT [FK_Transfer_RequestedBy]
GO
ALTER TABLE [dbo].[TransferRequests]  WITH CHECK ADD  CONSTRAINT [FK_Transfer_ToBranch] FOREIGN KEY([to_branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[TransferRequests] CHECK CONSTRAINT [FK_Transfer_ToBranch]
GO
ALTER TABLE [dbo].[TransferRequests]  WITH CHECK ADD  CONSTRAINT [FK_Transfer_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[TransferRequests] CHECK CONSTRAINT [FK_Transfer_Vehicle]
GO
ALTER TABLE [dbo].[UserRoles]  WITH CHECK ADD  CONSTRAINT [FK_UserRoles_Role] FOREIGN KEY([role_id])
REFERENCES [dbo].[Roles] ([id])
GO
ALTER TABLE [dbo].[UserRoles] CHECK CONSTRAINT [FK_UserRoles_Role]
GO
ALTER TABLE [dbo].[UserRoles]  WITH CHECK ADD  CONSTRAINT [FK_UserRoles_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[UserRoles] CHECK CONSTRAINT [FK_UserRoles_User]
GO
ALTER TABLE [dbo].[Users]  WITH CHECK ADD  CONSTRAINT [FK_Users_CreatedBy] FOREIGN KEY([created_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Users] CHECK CONSTRAINT [FK_Users_CreatedBy]
GO
ALTER TABLE [dbo].[VehicleImages]  WITH CHECK ADD  CONSTRAINT [FK_VImages_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[VehicleImages] CHECK CONSTRAINT [FK_VImages_Vehicle]
GO
ALTER TABLE [dbo].[VehicleMaintenanceHistory]  WITH CHECK ADD  CONSTRAINT [FK_VMH_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[VehicleMaintenanceHistory] CHECK CONSTRAINT [FK_VMH_Vehicle]
GO
ALTER TABLE [dbo].[VehicleReviews]  WITH CHECK ADD  CONSTRAINT [FK_VehicleReviews_booking] FOREIGN KEY([booking_id])
REFERENCES [dbo].[Bookings] ([id])
GO
ALTER TABLE [dbo].[VehicleReviews] CHECK CONSTRAINT [FK_VehicleReviews_booking]
GO
ALTER TABLE [dbo].[VehicleReviews]  WITH CHECK ADD  CONSTRAINT [FK_VehicleReviews_reviewer] FOREIGN KEY([reviewer_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[VehicleReviews] CHECK CONSTRAINT [FK_VehicleReviews_reviewer]
GO
ALTER TABLE [dbo].[VehicleReviews]  WITH CHECK ADD  CONSTRAINT [FK_VehicleReviews_vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
GO
ALTER TABLE [dbo].[VehicleReviews] CHECK CONSTRAINT [FK_VehicleReviews_vehicle]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [FK_Vehicles_Branch] FOREIGN KEY([branch_id])
REFERENCES [dbo].[Branches] ([id])
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [FK_Vehicles_Branch]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [FK_Vehicles_Category] FOREIGN KEY([category_id])
REFERENCES [dbo].[Categories] ([id])
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [FK_Vehicles_Category]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [FK_Vehicles_CreatedBy] FOREIGN KEY([created_by])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [FK_Vehicles_CreatedBy]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [FK_Vehicles_Subcategory] FOREIGN KEY([subcategory_id])
REFERENCES [dbo].[Subcategories] ([id])
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [FK_Vehicles_Subcategory]
GO
ALTER TABLE [dbo].[VehicleViewHistory]  WITH CHECK ADD  CONSTRAINT [FK_VViewHistory_User] FOREIGN KEY([user_id])
REFERENCES [dbo].[Users] ([id])
GO
ALTER TABLE [dbo].[VehicleViewHistory] CHECK CONSTRAINT [FK_VViewHistory_User]
GO
ALTER TABLE [dbo].[VehicleViewHistory]  WITH CHECK ADD  CONSTRAINT [FK_VViewHistory_Vehicle] FOREIGN KEY([vehicle_id])
REFERENCES [dbo].[Vehicles] ([id])
ON DELETE CASCADE
GO
ALTER TABLE [dbo].[VehicleViewHistory] CHECK CONSTRAINT [FK_VViewHistory_Vehicle]
GO
ALTER TABLE [dbo].[AIChatMessages]  WITH CHECK ADD  CONSTRAINT [CK_AIChatMsg_Sender] CHECK  (([sender_type]='ai' OR [sender_type]='user'))
GO
ALTER TABLE [dbo].[AIChatMessages] CHECK CONSTRAINT [CK_AIChatMsg_Sender]
GO
ALTER TABLE [dbo].[Bookings]  WITH CHECK ADD  CONSTRAINT [CK_Bookings_Status] CHECK  (([status]='Cancelled' OR [status]='Completed' OR [status]='Rescheduled' OR [status]='Confirmed' OR [status]='Pending' OR [status]='AwaitingContract'))
GO
ALTER TABLE [dbo].[Bookings] CHECK CONSTRAINT [CK_Bookings_Status]
GO
ALTER TABLE [dbo].[Branches]  WITH CHECK ADD  CONSTRAINT [CK_Branches_Status] CHECK  (([status]='inactive' OR [status]='active'))
GO
ALTER TABLE [dbo].[Branches] CHECK CONSTRAINT [CK_Branches_Status]
GO
ALTER TABLE [dbo].[BranchWorkingHours]  WITH CHECK ADD  CONSTRAINT [CK_BWH_DayOfWeek] CHECK  (([day_of_week]>=(0) AND [day_of_week]<=(6)))
GO
ALTER TABLE [dbo].[BranchWorkingHours] CHECK CONSTRAINT [CK_BWH_DayOfWeek]
GO
ALTER TABLE [dbo].[BranchWorkingHours]  WITH CHECK ADD  CONSTRAINT [CK_BWH_TimeOrder] CHECK  (([open_time]<>[close_time]))
GO
ALTER TABLE [dbo].[BranchWorkingHours] CHECK CONSTRAINT [CK_BWH_TimeOrder]
GO
ALTER TABLE [dbo].[Consultations]  WITH CHECK ADD  CONSTRAINT [CK_Consult_Priority] CHECK  (([priority]='high' OR [priority]='medium' OR [priority]='low'))
GO
ALTER TABLE [dbo].[Consultations] CHECK CONSTRAINT [CK_Consult_Priority]
GO
ALTER TABLE [dbo].[Consultations]  WITH CHECK ADD  CONSTRAINT [CK_Consult_Status] CHECK  (([status]='resolved' OR [status]='processing' OR [status]='pending'))
GO
ALTER TABLE [dbo].[Consultations] CHECK CONSTRAINT [CK_Consult_Status]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [CK_Deposits_Amount] CHECK  (([amount]>(0)))
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [CK_Deposits_Amount]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [CK_Deposits_ExpiryDate] CHECK  (([expiry_date]>=[deposit_date]))
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [CK_Deposits_ExpiryDate]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [CK_Deposits_PaymentGateway] CHECK  (([payment_gateway]='cash' OR [payment_gateway]='zalopay' OR [payment_gateway]='vnpay' OR [payment_gateway] IS NULL))
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [CK_Deposits_PaymentGateway]
GO
ALTER TABLE [dbo].[Deposits]  WITH CHECK ADD  CONSTRAINT [CK_Deposits_Status] CHECK  (([status]='AwaitingPayment' OR [status]='Expired' OR [status]='Cancelled' OR [status]='Refunded' OR [status]='RefundFailed' OR [status]='RefundPending' OR [status]='Converted' OR [status]='Confirmed' OR [status]='Pending'))
GO
ALTER TABLE [dbo].[Deposits] CHECK CONSTRAINT [CK_Deposits_Status]
GO
ALTER TABLE [dbo].[InstallmentApplications]  WITH CHECK ADD  CONSTRAINT [CK_InstallmentApplications_Status] CHECK  (([status]=N'CANCELLED' OR [status]=N'COMPLETED' OR [status]=N'DEPOSIT_PAID' OR [status]=N'DEPOSIT_PENDING' OR [status]=N'REJECTED' OR [status]=N'APPROVED' OR [status]=N'BANK_PROCESSING' OR [status]=N'PENDING_DOCUMENT' OR [status]=N'DRAFT'))
GO
ALTER TABLE [dbo].[InstallmentApplications] CHECK CONSTRAINT [CK_InstallmentApplications_Status]
GO
ALTER TABLE [dbo].[OrderPayments]  WITH CHECK ADD  CONSTRAINT [CK_OrderPay_Status] CHECK  (([status]='Refunded' OR [status]='Failed' OR [status]='Completed' OR [status]='Pending'))
GO
ALTER TABLE [dbo].[OrderPayments] CHECK CONSTRAINT [CK_OrderPay_Status]
GO
ALTER TABLE [dbo].[Orders]  WITH CHECK ADD  CONSTRAINT [CK_Orders_Status] CHECK  (([status]='Cancelled' OR [status]='Completed' OR [status]='Processing' OR [status]='Pending'))
GO
ALTER TABLE [dbo].[Orders] CHECK CONSTRAINT [CK_Orders_Status]
GO
ALTER TABLE [dbo].[Transactions]  WITH CHECK ADD  CONSTRAINT [CK_Trans_PaymentGateway] CHECK  (([payment_gateway]=N'cash' OR [payment_gateway]=N'zalopay' OR [payment_gateway]=N'vnpay'))
GO
ALTER TABLE [dbo].[Transactions] CHECK CONSTRAINT [CK_Trans_PaymentGateway]
GO
ALTER TABLE [dbo].[Transactions]  WITH CHECK ADD  CONSTRAINT [CK_Trans_Status] CHECK  (([status]='Failed' OR [status]='Completed' OR [status]='Pending'))
GO
ALTER TABLE [dbo].[Transactions] CHECK CONSTRAINT [CK_Trans_Status]
GO
ALTER TABLE [dbo].[Transactions]  WITH CHECK ADD  CONSTRAINT [CK_Trans_Type] CHECK  (([type]='Refund' OR [type]='Purchase' OR [type]='Deposit'))
GO
ALTER TABLE [dbo].[Transactions] CHECK CONSTRAINT [CK_Trans_Type]
GO
ALTER TABLE [dbo].[TransferApprovalHistory]  WITH CHECK ADD  CONSTRAINT [CK_TAH_Action] CHECK  (([action]='Rejected' OR [action]='Approved'))
GO
ALTER TABLE [dbo].[TransferApprovalHistory] CHECK CONSTRAINT [CK_TAH_Action]
GO
ALTER TABLE [dbo].[TransferRequests]  WITH CHECK ADD  CONSTRAINT [CK_Transfer_DiffBranch] CHECK  (([from_branch_id]<>[to_branch_id]))
GO
ALTER TABLE [dbo].[TransferRequests] CHECK CONSTRAINT [CK_Transfer_DiffBranch]
GO
ALTER TABLE [dbo].[TransferRequests]  WITH CHECK ADD  CONSTRAINT [CK_Transfer_Status] CHECK  (([status]='Completed' OR [status]='Rejected' OR [status]='Approved' OR [status]='Pending'))
GO
ALTER TABLE [dbo].[TransferRequests] CHECK CONSTRAINT [CK_Transfer_Status]
GO
ALTER TABLE [dbo].[Users]  WITH CHECK ADD  CONSTRAINT [CK_Users_Gender] CHECK  (([gender] IS NULL OR ([gender]=N'other' OR [gender]=N'female' OR [gender]=N'male')))
GO
ALTER TABLE [dbo].[Users] CHECK CONSTRAINT [CK_Users_Gender]
GO
ALTER TABLE [dbo].[Users]  WITH CHECK ADD  CONSTRAINT [CK_Users_Status] CHECK  (([status]='suspended' OR [status]='inactive' OR [status]='active'))
GO
ALTER TABLE [dbo].[Users] CHECK CONSTRAINT [CK_Users_Status]
GO
ALTER TABLE [dbo].[VehicleFuelTypes]  WITH CHECK ADD  CONSTRAINT [CK_VehicleFuelTypes_Status] CHECK  (([status]='inactive' OR [status]='active'))
GO
ALTER TABLE [dbo].[VehicleFuelTypes] CHECK CONSTRAINT [CK_VehicleFuelTypes_Status]
GO
ALTER TABLE [dbo].[VehicleReviews]  WITH CHECK ADD  CONSTRAINT [CK_VehicleReviews_rating] CHECK  (([rating]>=(1) AND [rating]<=(5)))
GO
ALTER TABLE [dbo].[VehicleReviews] CHECK CONSTRAINT [CK_VehicleReviews_rating]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [CK_Vehicles_Mileage] CHECK  (([mileage] IS NULL OR [mileage]>=(0)))
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [CK_Vehicles_Mileage]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [CK_Vehicles_Price] CHECK  (([price] IS NULL OR [price]>=(0)))
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [CK_Vehicles_Price]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [CK_Vehicles_Status] CHECK  (([status]='InTransfer' OR [status]='Hidden' OR [status]='Sold' OR [status]='Reserved' OR [status]='Available'))
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [CK_Vehicles_Status]
GO
ALTER TABLE [dbo].[Vehicles]  WITH CHECK ADD  CONSTRAINT [CK_Vehicles_Year] CHECK  (([year] IS NULL OR [year]>=(1900) AND [year]<=(2100)))
GO
ALTER TABLE [dbo].[Vehicles] CHECK CONSTRAINT [CK_Vehicles_Year]
GO
ALTER TABLE [dbo].[VehicleTransmissions]  WITH CHECK ADD  CONSTRAINT [CK_VehicleTransmissions_Status] CHECK  (([status]='inactive' OR [status]='active'))
GO
ALTER TABLE [dbo].[VehicleTransmissions] CHECK CONSTRAINT [CK_VehicleTransmissions_Status]
GO
CREATE TABLE [dbo].[MCP_Query_Log](
    [id]            BIGINT IDENTITY(1,1) NOT NULL,
    [session_id]    BIGINT NULL,
    [query_text]    NVARCHAR(500) NOT NULL,
    [source]        VARCHAR(20) NOT NULL,
    [tool_selected] VARCHAR(50) NULL,
    [params_json]   NVARCHAR(MAX) NULL,
    [success]       BIT NOT NULL,
    [result_count]  INT NOT NULL CONSTRAINT [DF_MCPQueryLog_ResultCount] DEFAULT ((0)),
    [latency_ms]    INT NOT NULL CONSTRAINT [DF_MCPQueryLog_Latency] DEFAULT ((0)),
    [created_at]    DATETIME2(3) NOT NULL CONSTRAINT [DF_MCPQueryLog_CreatedAt] DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [PK_MCP_Query_Log] PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_MCPQueryLog_Session] FOREIGN KEY ([session_id]) REFERENCES [dbo].[AIChatSessions]([id])
)
GO
CREATE NONCLUSTERED INDEX [IX_MCPQueryLog_CreatedAt] ON [dbo].[MCP_Query_Log]([created_at] DESC)
GO
CREATE NONCLUSTERED INDEX [IX_MCPQueryLog_SourceCreatedAt] ON [dbo].[MCP_Query_Log]([source], [created_at] DESC)
GO
CREATE NONCLUSTERED INDEX [IX_MCPQueryLog_ToolCreatedAt] ON [dbo].[MCP_Query_Log]([tool_selected], [created_at] DESC)
GO
USE [master]
GO
ALTER DATABASE [usedCars] SET  READ_WRITE 
GO

