// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;


interface OffchainBorrowingGauge {
    function add_measured_token(uint256 chain_id, address contract_address) external;
    function user_checkpoint(address borrower) external;
}


/**
 * @title Hundred's Controller Contract Mock
 * @author Hundred Finance
 */
contract HControllerMock {
    struct OutboundBorrow {
        uint chainId;
        address cToken;
        uint borrowBalance;
    }

    mapping(address => OutboundBorrow[]) public accountOutboundBorrows;
    mapping(uint => mapping(address => uint256)) public totalOutboundBorrows;
    mapping(uint => mapping(address => address)) public borrowGauges;

    function registerBorrowGauge(uint borrowChainId, address cToken, address gauge) public {
        require(totalOutboundBorrows[borrowChainId][cToken] == 0);

        borrowGauges[borrowChainId][cToken] = gauge;
        OffchainBorrowingGauge(gauge).add_measured_token(borrowChainId, cToken);
    }

    function _checkpointGauge(
        uint borrowChainId,
        address borrower,
        address cToken
    ) internal {
        address gauge = borrowGauges[borrowChainId][cToken];
        if (gauge == address(0)) return;

        OffchainBorrowingGauge(gauge).user_checkpoint(borrower);
    }

    function increaseBorrowPosition(
        uint borrowChainId,
        address borrower,
        address cToken,
        uint borrowAmount
    ) public {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];

        uint len = borrowPositions.length;
        uint positionIndex = len;
        for (uint i = 0; i < len; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                positionIndex = i;
                break;
            }
        }

        if (positionIndex < len) {
            accountOutboundBorrows[borrower][positionIndex].borrowBalance += borrowAmount;
        } else {
            OutboundBorrow memory borrowPosition;

            borrowPosition.chainId = borrowChainId;
            borrowPosition.cToken = cToken;
            borrowPosition.borrowBalance = borrowAmount;

            accountOutboundBorrows[borrower].push(borrowPosition);
        }

        totalOutboundBorrows[borrowChainId][cToken] += borrowAmount;
        _checkpointGauge(borrowChainId, borrower, cToken);
    }

    function reduceBorrowPosition(
        uint borrowChainId,
        address borrower,
        address cToken,
        uint repayAmount
    ) public {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];

        uint len = borrowPositions.length;
        uint positionIndex = len;
        for (uint i = 0; i < len; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                positionIndex = i;
                break;
            }
        }

        if (positionIndex < len) {
            accountOutboundBorrows[borrower][positionIndex].borrowBalance -= repayAmount;
        }

        totalOutboundBorrows[borrowChainId][cToken] -= repayAmount;
        _checkpointGauge(borrowChainId, borrower, cToken);
    }

    function resetBorrowPosition(
        uint borrowChainId,
        address borrower,
        address cToken,
        uint borrowBalance
    ) internal {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];

        uint len = borrowPositions.length;
        uint positionIndex = len;
        for (uint i = 0; i < len; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                positionIndex = i;
                break;
            }
        }

        if (positionIndex < len) {
            accountOutboundBorrows[borrower][positionIndex].borrowBalance = borrowBalance;
        }
    }

    function accountOffchainBorrows(uint256 borrowChainId, address cToken, address borrower) public view returns (uint256 total) {
        OutboundBorrow[] memory borrowPositions = accountOutboundBorrows[borrower];
        for (uint i = 0; i < borrowPositions.length; i++) {
            if (borrowPositions[i].cToken == cToken && borrowPositions[i].chainId == borrowChainId) {
                total += borrowPositions[i].borrowBalance;
                break;
            }
        }
    }

    function totalOffchainBorrows(uint256 borrowChainId, address cToken) public view returns (uint256) {
        return totalOutboundBorrows[borrowChainId][cToken];
    }
}
